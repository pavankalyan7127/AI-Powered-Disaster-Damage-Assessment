"""
xBD/xView2 Dataset Discovery, Multi-Tier Parsing, Restartable Crop Generation, and PyTorch Dataset Pipeline.
"""

import os
import json
import glob
import random
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import torch
from torch.utils.data import Dataset
from PIL import Image
from shapely.wkt import loads as wkt_loads
from shapely.geometry import Polygon

DAMAGE_MAPPING = {
    "no-damage": 0,
    "minor-damage": 1,
    "major-damage": 2,
    "destroyed": 3
}

def parse_wkt_polygon(wkt_str: str) -> Optional[Polygon]:
    """Safely parse WKT string into Shapely Polygon."""
    try:
        poly = wkt_loads(wkt_str)
        if poly.is_valid:
            return poly
        return poly.buffer(0)
    except Exception:
        return None

def crop_building(
    img: Image.Image,
    bounds: Tuple[float, float, float, float],
    padding: int = 10
) -> Image.Image:
    """
    Safely crop building region with padding while respecting image boundaries.
    bounds: (minx, miny, maxx, maxy)
    """
    width, height = img.size
    minx, miny, maxx, maxy = bounds
    
    crop_minx = max(0, int(minx) - padding)
    crop_miny = max(0, int(miny) - padding)
    crop_maxx = min(width, int(maxx) + padding)
    crop_maxy = min(height, int(maxy) + padding)
    
    return img.crop((crop_minx, crop_miny, crop_maxx, crop_maxy))

def process_xbd_dataset(
    raw_dir: str,
    output_dir: str,
    labeled_subdirs: Optional[List[str]] = None,
    crop_size: Tuple[int, int] = (128, 128),
    padding: int = 10,
    min_crop_size: int = 10,
    splits: Tuple[float, float, float] = (0.70, 0.15, 0.15),
    seed: int = 42,
    limit: Optional[int] = None,
    subset_manifest: Optional[str] = None,
    validate_only: bool = False
) -> Dict[str, Any]:
    """
    Scans tier directories in raw_dir (or loads selected subset manifest if provided),
    pairs pre/post disaster images, reads features['xy'] WKT polygons and damage subtypes,
    generates non-overlapping building crop pairs grouped by original image pair, and outputs split manifests.
    """
    if labeled_subdirs is None:
        labeled_subdirs = ["tier1", "tier3", "hold", "test"]

    random.seed(seed)

    if not os.path.exists(raw_dir):
        return {
            "status": "error",
            "message": f"Raw dataset directory '{raw_dir}' does not exist. Please place xBD files under '{raw_dir}'."
        }

    scanned_subdirs = []
    skipped_counts = {
        "missing_pairs": 0,
        "json_read_errors": 0,
        "unmapped_damage": 0,
        "invalid_polygons": 0,
        "small_polygons": 0
    }

    discovered_pairs: List[Dict[str, str]] = []

    # Option A: Load from subset manifest if provided
    if subset_manifest and os.path.exists(subset_manifest):
        print(f"[INFO] Loading class-aware subset manifest from: '{subset_manifest}'")
        with open(subset_manifest, 'r') as f:
            manifest_data = json.load(f)

        pairs_list = manifest_data.get("selected_pairs", [])
        for item in pairs_list:
            discovered_pairs.append({
                "subdir": item["tier"],
                "base_name": item["base_name"],
                "post_json_path": item["post_json"],
                "pre_img_path": item["pre_image"],
                "post_img_path": item["post_image"],
                "group_key": item["pair_id"]
            })
            if item["tier"] not in scanned_subdirs:
                scanned_subdirs.append(item["tier"])

    # Option B: Standard tier directory discovery
    else:
        for subdir in labeled_subdirs:
            tier_dir = os.path.join(raw_dir, subdir)
            labels_dir = os.path.join(tier_dir, "labels")
            images_dir = os.path.join(tier_dir, "images")

            if not (os.path.exists(labels_dir) and os.path.exists(images_dir)):
                continue

            scanned_subdirs.append(subdir)
            post_json_files = glob.glob(os.path.join(labels_dir, "*_post_disaster.json"))

            for post_json_path in post_json_files:
                base_name = os.path.basename(post_json_path).replace("_post_disaster.json", "")
                pre_json_path = os.path.join(labels_dir, f"{base_name}_pre_disaster.json")
                pre_img_path = os.path.join(images_dir, f"{base_name}_pre_disaster.png")
                post_img_path = os.path.join(images_dir, f"{base_name}_post_disaster.png")

                if not (os.path.exists(pre_json_path) and os.path.exists(pre_img_path) and os.path.exists(post_img_path)):
                    skipped_counts["missing_pairs"] += 1
                    continue

                discovered_pairs.append({
                    "subdir": subdir,
                    "base_name": base_name,
                    "post_json_path": post_json_path,
                    "pre_img_path": pre_img_path,
                    "post_img_path": post_img_path,
                    "group_key": f"{subdir}_{base_name}"
                })

    if not scanned_subdirs:
        return {
            "status": "error",
            "message": f"No valid labeled subdirectories found under '{raw_dir}'. Expected tier folders such as {labeled_subdirs} containing 'images/' and 'labels/'."
        }

    total_pairs_found = len(discovered_pairs)
    if total_pairs_found == 0:
        return {
            "status": "empty",
            "scanned_subdirs": scanned_subdirs,
            "image_pairs_found": 0,
            "skipped": skipped_counts,
            "samples": 0
        }

    # Apply limit if specified
    if limit is not None and limit > 0:
        discovered_pairs = discovered_pairs[:limit]

    # Grouped Split (by original image pair)
    group_keys = sorted(list(set(pair["group_key"] for pair in discovered_pairs)))
    random.shuffle(group_keys)

    total_groups = len(group_keys)
    train_end = int(total_groups * splits[0])
    val_end = train_end + int(total_groups * splits[1])

    train_groups = set(group_keys[:train_end])
    val_groups = set(group_keys[train_end:val_end])

    group_split_map = {}
    for gk in group_keys:
        if gk in train_groups:
            group_split_map[gk] = "train"
        elif gk in val_groups:
            group_split_map[gk] = "val"
        else:
            group_split_map[gk] = "test"

    if validate_only:
        valid_pairs_count = 0
        total_valid_buildings = 0
        for pair in discovered_pairs:
            try:
                with open(pair["post_json_path"], 'r') as f:
                    post_data = json.load(f)
                buildings = post_data.get("features", {}).get("xy", [])
                valid_b = 0
                for building in buildings:
                    properties = building.get("properties", {})
                    subtype = properties.get("subtype", "un-classified").lower()
                    if subtype not in DAMAGE_MAPPING:
                        continue
                    wkt_str = building.get("wkt", "")
                    poly = parse_wkt_polygon(wkt_str)
                    if poly is None or poly.is_empty:
                        continue
                    minx, miny, maxx, maxy = poly.bounds
                    if (maxx - minx) < min_crop_size or (maxy - miny) < min_crop_size:
                        continue
                    valid_b += 1
                if valid_b > 0:
                    valid_pairs_count += 1
                    total_valid_buildings += valid_b
            except Exception:
                skipped_counts["json_read_errors"] += 1

        return {
            "status": "validated",
            "scanned_subdirs": scanned_subdirs,
            "image_pairs_found": total_pairs_found,
            "pairs_validated": len(discovered_pairs),
            "valid_image_pairs": valid_pairs_count,
            "estimated_buildings": total_valid_buildings,
            "skipped": skipped_counts
        }

    manifest = {"train": [], "val": [], "test": []}
    existing_crops_skipped = 0
    new_crops_generated = 0

    for idx, pair in enumerate(discovered_pairs):
        subdir = pair["subdir"]
        base_name = pair["base_name"]
        gk = pair["group_key"]
        split_name = group_split_map[gk]
        split_dir = os.path.join(output_dir, split_name)
        os.makedirs(split_dir, exist_ok=True)

        try:
            with open(pair["post_json_path"], 'r') as f:
                post_data = json.load(f)

            buildings = post_data.get("features", {}).get("xy", [])
            if not buildings:
                continue

            pre_img = None
            post_img = None

            for b_idx, building in enumerate(buildings):
                properties = building.get("properties", {})
                subtype = properties.get("subtype", "un-classified").lower()

                if subtype not in DAMAGE_MAPPING:
                    skipped_counts["unmapped_damage"] += 1
                    continue

                wkt_str = building.get("wkt", "")
                poly = parse_wkt_polygon(wkt_str)
                if poly is None or poly.is_empty:
                    skipped_counts["invalid_polygons"] += 1
                    continue

                minx, miny, maxx, maxy = poly.bounds
                if (maxx - minx) < min_crop_size or (maxy - miny) < min_crop_size:
                    skipped_counts["small_polygons"] += 1
                    continue

                building_id = f"{subdir}_{base_name}_b{b_idx}"
                pre_path = os.path.join(split_dir, f"{building_id}_pre.png")
                post_path = os.path.join(split_dir, f"{building_id}_post.png")

                if os.path.exists(pre_path) and os.path.exists(post_path):
                    existing_crops_skipped += 1
                else:
                    if pre_img is None:
                        pre_img = Image.open(pair["pre_img_path"]).convert("RGB")
                        post_img = Image.open(pair["post_img_path"]).convert("RGB")

                    bounds = (minx, miny, maxx, maxy)
                    pre_crop = crop_building(pre_img, bounds, padding=padding).resize(crop_size, Image.Resampling.BILINEAR)
                    post_crop = crop_building(post_img, bounds, padding=padding).resize(crop_size, Image.Resampling.BILINEAR)

                    pre_crop.save(pre_path)
                    post_crop.save(post_path)
                    new_crops_generated += 1

                manifest[split_name].append({
                    "sample_id": building_id,
                    "tier": subdir,
                    "image_pair_prefix": base_name,
                    "pre_path": pre_path,
                    "post_path": post_path,
                    "label": DAMAGE_MAPPING[subtype],
                    "label_str": subtype
                })

            if pre_img is not None:
                pre_img.close()
                post_img.close()

        except Exception:
            skipped_counts["json_read_errors"] += 1
            continue

    for split_name in ["train", "val", "test"]:
        manifest_path = os.path.join(output_dir, f"{split_name}_manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest[split_name], f, indent=2)

    total_samples = len(manifest["train"]) + len(manifest["val"]) + len(manifest["test"])

    return {
        "status": "success",
        "scanned_subdirs": scanned_subdirs,
        "image_pairs_found": total_pairs_found,
        "image_pairs_processed": len(discovered_pairs),
        "unique_image_groups": total_groups,
        "samples": total_samples,
        "new_crops_generated": new_crops_generated,
        "existing_crops_skipped": existing_crops_skipped,
        "train": len(manifest["train"]),
        "val": len(manifest["val"]),
        "test": len(manifest["test"]),
        "skipped": skipped_counts
    }

class BuildingDamageDataset(Dataset):
    """PyTorch Dataset loading pre/post cropped building pairs."""
    def __init__(self, manifest_path: str, transform=None):
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(
                f"Manifest file not found at '{manifest_path}'. "
                f"Please run 'python preprocess.py' to generate preprocessed data manifests first."
            )
        with open(manifest_path, 'r') as f:
            self.items = json.load(f)
        self.transform = transform

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        item = self.items[idx]
        pre_img = Image.open(item["pre_path"]).convert("RGB")
        post_img = Image.open(item["post_path"]).convert("RGB")

        pre_np = np.array(pre_img, dtype=np.float32) / 255.0
        post_np = np.array(post_img, dtype=np.float32) / 255.0

        pre_tensor = torch.from_numpy(pre_np).permute(2, 0, 1)
        post_tensor = torch.from_numpy(post_np).permute(2, 0, 1)

        # Standard ImageNet Normalization
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)

        pre_tensor = (pre_tensor - mean) / std
        post_tensor = (post_tensor - mean) / std
        label_tensor = torch.tensor(item["label"], dtype=torch.long)

        return pre_tensor, post_tensor, label_tensor
