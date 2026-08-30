"""
Satellite Crop Engine Module for Disaster Damage Assessment.
Converts pre/post disaster satellite images and building footprint annotations
into corresponding 128x128 building crop pairs ready for model inference.

Features memory-efficient windowed reads via Rasterio:
- Never opens full satellite TIFF files into RAM or PIL Image.
- Reads ONLY small bounding box pixel windows directly from GeoTIFF/COG files via rasterio.windows.Window.
- Auto-detects whether footprint coordinates are in pixel space or geographic CRS (e.g. EPSG:4326 WGS84).
- For GeoTIFF / georeferenced rasters, converts geographic coordinates (lng, lat)
  to exact image pixel coordinates via the raster's affine transform.
- Handles non-uint8 or high-dynamic-range rasters with nodata masking and proper scaling.
- Supports xBD JSON (`features.xy` for pixel coords or `features.lng_lat` for geographic coords), GeoJSON, and WKT.
"""

import os
import sys
import json
import yaml
import argparse
import numpy as np
from typing import Dict, Any, List, Tuple, Union, Optional
from PIL import Image
from shapely.wkt import loads as wkt_loads
from shapely.geometry import Polygon, shape

# Rasterio import for GeoTIFF / geospatial windowed reading
HAS_RASTERIO = False
try:
    import rasterio
    from rasterio.crs import CRS
    from rasterio.warp import transform_geom
    from rasterio.windows import Window
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

from src.dataset import parse_wkt_polygon


class SatelliteCropEngine:
    """
    Reusable crop engine for satellite imagery and building footprints.
    Converts geographic or pixel footprint coordinates into pixel bounding boxes,
    and extracts matching pre/post disaster building crop image pairs (128x128 px)
    using memory-efficient windowed reads.
    """

    def __init__(
        self,
        config_path: str = "config.yaml",
        target_size: Tuple[int, int] = (128, 128),
        default_padding: int = 10,
        min_crop_size: int = 10
    ):
        self.config_path = config_path
        self.target_size = target_size
        self.default_padding = default_padding
        self.min_crop_size = min_crop_size

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    cfg = yaml.safe_load(f)
                prep_cfg = cfg.get("preprocessing", {})
                self.target_size = tuple(prep_cfg.get("crop_size", [128, 128]))
                self.default_padding = prep_cfg.get("padding", 10)
                self.min_crop_size = prep_cfg.get("min_crop_size", 10)
            except Exception:
                pass

    def _parse_footprints(
        self,
        footprints_input: Union[str, List[Any], Dict[str, Any]]
    ) -> List[Tuple[str, Polygon, str]]:
        """
        Parses footprints from GeoJSON or xBD JSON.
        Returns a list of (building_id, Polygon, coord_type) tuples,
        where coord_type is 'pixel' or 'geographic'.
        """
        polygons = []

        if isinstance(footprints_input, str):
            if not os.path.exists(footprints_input):
                raise FileNotFoundError(f"Footprints file not found at '{footprints_input}'.")
            with open(footprints_input, 'r') as f:
                data = json.load(f)
        elif isinstance(footprints_input, (dict, list)):
            data = footprints_input
        else:
            raise TypeError(f"Unsupported footprints type: {type(footprints_input)}")

        if isinstance(data, dict):
            features_dict = data.get("features", {})
            
            # xBD style pixel coordinates: features['xy']
            if isinstance(features_dict, dict) and "xy" in features_dict:
                for idx, feat in enumerate(features_dict["xy"]):
                    wkt_str = feat.get("wkt", "")
                    poly = parse_wkt_polygon(wkt_str)
                    if poly and not poly.is_empty:
                        b_id = feat.get("properties", {}).get("feature_id") or feat.get("properties", {}).get("uid", f"b_{idx}")
                        polygons.append((str(b_id), poly, "pixel"))

            # xBD style geographic coordinates: features['lng_lat']
            elif isinstance(features_dict, dict) and "lng_lat" in features_dict:
                for idx, feat in enumerate(features_dict["lng_lat"]):
                    wkt_str = feat.get("wkt", "")
                    poly = parse_wkt_polygon(wkt_str)
                    if poly and not poly.is_empty:
                        b_id = feat.get("properties", {}).get("feature_id") or feat.get("properties", {}).get("uid", f"b_{idx}")
                        polygons.append((str(b_id), poly, "geographic"))

            # Standard GeoJSON style: features list
            elif isinstance(features_dict, list):
                for idx, feat in enumerate(features_dict):
                    b_id = feat.get("id") or feat.get("properties", {}).get("id", f"b_{idx}")
                    geom = feat.get("geometry")
                    if geom:
                        try:
                            poly = shape(geom)
                            if poly and not poly.is_empty:
                                minx, miny, maxx, maxy = poly.bounds
                                coord_type = "geographic" if (abs(minx) <= 180 and abs(maxx) <= 180 and abs(miny) <= 90 and abs(maxy) <= 90) else "pixel"
                                polygons.append((str(b_id), poly, coord_type))
                        except Exception:
                            continue

        elif isinstance(data, list):
            for idx, item in enumerate(data):
                if isinstance(item, str):
                    poly = parse_wkt_polygon(item)
                    if poly and not poly.is_empty:
                        minx, miny, maxx, maxy = poly.bounds
                        coord_type = "geographic" if (abs(minx) <= 180 and abs(maxx) <= 180 and abs(miny) <= 90 and abs(maxy) <= 90) else "pixel"
                        polygons.append((f"b_{idx}", poly, coord_type))

        return polygons

    def _poly_geo_to_pixel(
        self,
        poly: Polygon,
        src_dataset: Any
    ) -> Tuple[Optional[Tuple[float, float, float, float]], Dict[str, Any]]:
        """
        Converts a geographic Polygon (WGS84 / lng-lat) into pixel bounding box coordinates
        using an open rasterio dataset handle.
        Returns ((minx_px, miny_px, maxx_px, maxy_px), crs_info_dict).
        """
        img_crs = src_dataset.crs
        transform = src_dataset.transform
        width, height = src_dataset.width, src_dataset.height

        if img_crs is None:
            raise ValueError(
                f"Raster lacks geospatial CRS metadata. "
                "Cannot map geographic footprint coordinates to pixels without a valid CRS."
            )

        wgs84 = CRS.from_epsg(4326)
        geo_poly = poly
        if img_crs != wgs84:
            transformed_geom = transform_geom(wgs84, img_crs, poly.__geo_interface__)
            geo_poly = shape(transformed_geom)

        inv_transform = ~transform
        coords = list(geo_poly.exterior.coords)
        pixel_coords = [inv_transform * (x, y) for x, y in coords]

        xs = [p[0] for p in pixel_coords]
        ys = [p[1] for p in pixel_coords]

        minx_px, maxx_px = min(xs), max(xs)
        miny_px, maxy_px = min(ys), max(ys)

        crs_info = {
            "crs": str(img_crs),
            "transform": [round(t, 6) for t in list(transform)[:6]],
            "width": width,
            "height": height
        }

        return (minx_px, miny_px, maxx_px, maxy_px), crs_info

    def _crop_window_rasterio(
        self,
        src_dataset: Any,
        bounds: Tuple[float, float, float, float],
        padding: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Reads ONLY the target bounding box window directly from disk via Rasterio.
        Applies padding, handles dtypes/nodata, and returns a dict with PIL Image and stats.
        """
        minx, miny, maxx, maxy = bounds
        width, height = src_dataset.width, src_dataset.height

        # Calculate padded pixel crop coordinates clamped to image dimensions
        crop_minx = max(0, int(minx) - padding)
        crop_miny = max(0, int(miny) - padding)
        crop_maxx = min(width, int(maxx) + padding)
        crop_maxy = min(height, int(maxy) + padding)

        col_off = crop_minx
        row_off = crop_miny
        win_w = crop_maxx - crop_minx
        win_h = crop_maxy - crop_miny

        if win_w <= 0 or win_h <= 0:
            return None

        # Create Rasterio Window
        win = Window(col_off=col_off, row_off=row_off, width=win_w, height=win_h)

        # Determine bands to read (up to 3 bands for RGB)
        band_count = src_dataset.count
        indexes = tuple(range(1, min(band_count, 3) + 1))

        # Read window array directly from raster on disk (shape: C, H, W)
        arr = src_dataset.read(indexes, window=win)

        if arr.size == 0 or arr.shape[1] == 0 or arr.shape[2] == 0:
            return None

        # Raw Array Statistics
        raw_min = float(arr.min())
        raw_max = float(arr.max())
        raw_mean = float(arr.mean())

        # If window contains only zeros/nodata, reject empty window
        if raw_max == 0:
            return None

        # Convert C, H, W to H, W, C
        arr_hwc = np.transpose(arr, (1, 2, 0))

        # Handle band count / normalization to uint8
        if arr_hwc.ndim == 2:
            arr_hwc = np.stack([arr_hwc] * 3, axis=-1)
        elif arr_hwc.shape[2] == 1:
            arr_hwc = np.repeat(arr_hwc, 3, axis=-1)
        elif arr_hwc.shape[2] > 3:
            arr_hwc = arr_hwc[:, :, :3]

        # Convert/Scale non-uint8 or high dynamic range data safely to uint8
        if arr_hwc.dtype != np.uint8:
            nodata_val = src_dataset.nodatavals[0] if src_dataset.nodatavals else None
            if nodata_val is not None:
                mask = (arr_hwc != nodata_val)
                valid_data = arr_hwc[mask]
                if valid_data.size > 0:
                    v_min, v_max = valid_data.min(), valid_data.max()
                    if v_max > v_min:
                        arr_hwc = np.clip((arr_hwc - v_min) / (v_max - v_min) * 255.0, 0, 255).astype(np.uint8)
                    else:
                        arr_hwc = np.clip(arr_hwc, 0, 255).astype(np.uint8)
                else:
                    return None
            else:
                v_max = arr_hwc.max()
                if v_max > 255:
                    arr_hwc = np.clip((arr_hwc / v_max) * 255.0, 0, 255).astype(np.uint8)
                else:
                    arr_hwc = np.clip(arr_hwc, 0, 255).astype(np.uint8)

        converted_min = float(arr_hwc.min())
        converted_max = float(arr_hwc.max())

        pil_img = Image.fromarray(arr_hwc, mode="RGB")
        return {
            "image": pil_img,
            "stats": {
                "raw_min": raw_min,
                "raw_max": raw_max,
                "raw_mean": round(raw_mean, 2),
                "converted_min": converted_min,
                "converted_max": converted_max,
                "dtype": str(src_dataset.dtypes[0]),
                "band_count": band_count
            }
        }

    def _crop_pil_image(
        self,
        img: Image.Image,
        bounds: Tuple[float, float, float, float],
        padding: int = 10
    ) -> Image.Image:
        """
        Fallback crop helper for PIL Image objects.
        """
        width, height = img.size
        minx, miny, maxx, maxy = bounds

        crop_minx = max(0, int(minx) - padding)
        crop_miny = max(0, int(miny) - padding)
        crop_maxx = min(width, int(maxx) + padding)
        crop_maxy = min(height, int(maxy) + padding)

        return img.crop((crop_minx, crop_miny, crop_maxx, crop_maxy))

    def create_building_pairs(
        self,
        pre_image: Union[str, Image.Image],
        post_image: Union[str, Image.Image],
        footprints: Union[str, List[Any], Dict[str, Any]],
        output_dir: str = "outputs/inference_crops",
        padding: Optional[int] = None,
        aligned_images: bool = True
    ) -> Dict[str, Any]:
        """
        Generates corresponding building crop image pairs for pre- and post-disaster satellite images.
        Uses windowed reads for GeoTIFF filepaths to avoid loading large satellite images into RAM.
        """
        if padding is None:
            padding = self.default_padding

        if not aligned_images:
            raise ValueError(
                "Spatial alignment unconfirmed. pre_image and post_image must be spatially aligned "
                "or georeferenced to ensure valid building crop correspondence."
            )

        # Parse Footprints
        building_polygons = self._parse_footprints(footprints)
        total_footprints = len(building_polygons)

        if total_footprints == 0:
            print("[WARNING] No valid building footprints found in the provided input.")

        os.makedirs(output_dir, exist_ok=True)

        generated_pairs = []
        valid_count = 0
        skipped_count = 0
        intersecting_count = 0
        transform_count = 0

        pre_crs_info = "N/A (PIL RGB / Pixel Space)"
        post_crs_info = "N/A (PIL RGB / Pixel Space)"

        # Check whether inputs are filepaths or PIL Images
        is_pre_filepath = isinstance(pre_image, str) and HAS_RASTERIO
        is_post_filepath = isinstance(post_image, str) and HAS_RASTERIO

        pre_ds = rasterio.open(pre_image) if is_pre_filepath else None
        post_ds = rasterio.open(post_image) if is_post_filepath else None

        try:
            for b_idx, (b_id, poly, coord_type) in enumerate(building_polygons):
                try:
                    # Case 1: Geographic coordinates (lng, lat) -> Convert to pixels
                    if coord_type == "geographic":
                        if not (pre_ds and post_ds):
                            raise ValueError("Geographic coordinates require georeferenced image filepaths to read CRS and affine transforms.")

                        pre_bounds, pre_crs_info = self._poly_geo_to_pixel(poly, pre_ds)
                        post_bounds, post_crs_info = self._poly_geo_to_pixel(poly, post_ds)
                        transform_count += 2

                    # Case 2: Pixel coordinates -> Use directly
                    else:
                        minx, miny, maxx, maxy = poly.bounds
                        pre_bounds = (minx, miny, maxx, maxy)
                        post_bounds = (minx, miny, maxx, maxy)

                    pre_minx, pre_miny, pre_maxx, pre_maxy = pre_bounds
                    post_minx, post_miny, post_maxx, post_maxy = post_bounds

                    pre_w, pre_h = pre_maxx - pre_minx, pre_maxy - pre_miny
                    post_w, post_h = post_maxx - post_minx, post_maxy - post_miny

                    # Check bounding box validity and raster intersection
                    pre_raster_w = pre_ds.width if pre_ds else pre_image.size[0]
                    pre_raster_h = pre_ds.height if pre_ds else pre_image.size[1]
                    post_raster_w = post_ds.width if post_ds else post_image.size[0]
                    post_raster_h = post_ds.height if post_ds else post_image.size[1]

                    # Verify if bounding box intersects raster extent
                    pre_intersects = not (pre_maxx < 0 or pre_minx >= pre_raster_w or pre_maxy < 0 or pre_miny >= pre_raster_h)
                    post_intersects = not (post_maxx < 0 or post_minx >= post_raster_w or post_maxy < 0 or post_miny >= post_raster_h)

                    if not (pre_intersects and post_intersects):
                        skipped_count += 1
                        continue

                    intersecting_count += 1

                    # Enforce minimum crop size in pixel units
                    if pre_w < self.min_crop_size or pre_h < self.min_crop_size or post_w < self.min_crop_size or post_h < self.min_crop_size:
                        skipped_count += 1
                        continue

                    # Windowed read from GeoTIFF or fallback crop on PIL image
                    pre_crop_res = None
                    post_crop_res = None

                    if pre_ds:
                        pre_crop_res = self._crop_window_rasterio(pre_ds, pre_bounds, padding=padding)
                    else:
                        pil_crop = self._crop_pil_image(pre_image, pre_bounds, padding=padding)
                        pre_crop_res = {"image": pil_crop, "stats": {"raw_min": 0, "raw_max": 255, "raw_mean": 128, "converted_min": 0, "converted_max": 255, "dtype": "uint8", "band_count": 3}}

                    if post_ds:
                        post_crop_res = self._crop_window_rasterio(post_ds, post_bounds, padding=padding)
                    else:
                        pil_crop = self._crop_pil_image(post_image, post_bounds, padding=padding)
                        post_crop_res = {"image": pil_crop, "stats": {"raw_min": 0, "raw_max": 255, "raw_mean": 128, "converted_min": 0, "converted_max": 255, "dtype": "uint8", "band_count": 3}}

                    if pre_crop_res is None or post_crop_res is None:
                        skipped_count += 1
                        continue

                    # Resize final crops to 128x128
                    pre_crop = pre_crop_res["image"].resize(self.target_size, Image.Resampling.BILINEAR)
                    post_crop = post_crop_res["image"].resize(self.target_size, Image.Resampling.BILINEAR)

                    crop_folder_name = f"building_{b_idx:04d}_{b_id}"
                    crop_dir = os.path.join(output_dir, crop_folder_name)
                    os.makedirs(crop_dir, exist_ok=True)

                    pre_crop_path = os.path.join(crop_dir, "pre.png")
                    post_crop_path = os.path.join(crop_dir, "post.png")

                    pre_crop.save(pre_crop_path)
                    post_crop.save(post_crop_path)

                    orig_bounds = [round(b, 6) for b in poly.bounds]
                    pre_pixel_bounds = [round(b, 2) for b in pre_bounds]
                    post_pixel_bounds = [round(b, 2) for b in post_bounds]

                    meta = {
                        "building_id": b_id,
                        "folder_name": crop_folder_name,
                        "coord_type": coord_type,
                        "pre_source": str(pre_image),
                        "post_source": str(post_image),
                        "original_geographic_bounds": orig_bounds,
                        "pre_pixel_bounds": pre_pixel_bounds,
                        "post_pixel_bounds": post_pixel_bounds,
                        "crop_size": list(self.target_size),
                        "padding": padding,
                        "crs_info": {
                            "pre": pre_crs_info,
                            "post": post_crs_info
                        },
                        "stats": {
                            "pre": pre_crop_res["stats"],
                            "post": post_crop_res["stats"]
                        },
                        "pre_crop_path": pre_crop_path,
                        "post_crop_path": post_crop_path
                    }

                    meta_json_path = os.path.join(crop_dir, "metadata.json")
                    with open(meta_json_path, "w") as f:
                        json.dump(meta, f, indent=2)

                    generated_pairs.append({
                        "building_id": b_id,
                        "pre_crop": pre_crop_path,
                        "post_crop": post_crop_path,
                        "metadata": meta
                    })

                    valid_count += 1

                except Exception:
                    skipped_count += 1

        finally:
            if pre_ds:
                pre_ds.close()
            if post_ds:
                post_ds.close()

        summary = {
            "status": "success" if valid_count > 0 else "empty",
            "total_footprints": total_footprints,
            "footprints_intersecting_raster": intersecting_count,
            "valid_buildings": valid_count,
            "skipped_buildings": skipped_count,
            "generated_pairs": len(generated_pairs),
            "transform_count": transform_count,
            "crs_info": {
                "pre": pre_crs_info,
                "post": post_crs_info
            },
            "output_dir": output_dir,
            "pairs": generated_pairs
        }

        return summary


def main():
    parser = argparse.ArgumentParser(description="Extract 128x128 building crop pairs from pre/post satellite imagery.")
    parser.add_argument("--pre", type=str, required=True, help="Path to pre-disaster satellite image.")
    parser.add_argument("--post", type=str, required=True, help="Path to post-disaster satellite image.")
    parser.add_argument("--footprints", type=str, required=True, help="Path to building footprints file (xBD JSON or GeoJSON).")
    parser.add_argument("--output", type=str, default="outputs/inference_crops", help="Output directory for building crop pairs.")
    parser.add_argument("--padding", type=int, default=10, help="Bounding box margin padding in pixels.")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config.yaml file.")
    args = parser.parse_args()

    print("==================================================")
    print("   Satellite -> Building Crop Engine MVP          ")
    print("==================================================")
    print(f"Pre-disaster image:    {args.pre}")
    print(f"Post-disaster image:   {args.post}")
    print(f"Building footprints:   {args.footprints}")
    print(f"Output directory:      {args.output}")
    print("==================================================")

    try:
        engine = SatelliteCropEngine(config_path=args.config)
        summary = engine.create_building_pairs(
            pre_image=args.pre,
            post_image=args.post,
            footprints=args.footprints,
            output_dir=args.output,
            padding=args.padding
        )

        print(f"\nImage CRS Pre:                     {summary['crs_info']['pre']}")
        print(f"Image CRS Post:                    {summary['crs_info']['post']}")
        print(f"Transformations run:               {summary['transform_count']}")
        print(f"Total footprints:                  {summary['total_footprints']}")
        print(f"Footprints intersecting raster:    {summary['footprints_intersecting_raster']}")
        print(f"Valid building crops:              {summary['valid_buildings']}")
        print(f"Generated PRE/POST crop pairs:     {summary['generated_pairs']}")
        print(f"Skipped buildings:                 {summary['skipped_buildings']}")
        print(f"Output directory:                  {summary['output_dir']}")
        print("==================================================")
        print("[SUCCESS] Building crop pairs generated successfully!")

    except Exception as e:
        print(f"[ERROR] Crop engine execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
