"""
Standalone CLI script for offline xBD dataset parsing and crop preprocessing.
"""

import os
import sys
import yaml
import argparse
from src.dataset import process_xbd_dataset

def main():
    parser = argparse.ArgumentParser(description="Preprocess xBD multi-tier dataset into cropped building pairs.")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config.yaml file.")
    parser.add_argument("--limit", type=int, default=None, help="Limit preprocessing to N image pairs for fast testing.")
    parser.add_argument("--subset-manifest", type=str, default=None, help="Path to selected subset manifest JSON file.")
    parser.add_argument("--validate-only", action="store_true", help="Inspect dataset structure and annotations without saving images.")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"[ERROR] Configuration file '{args.config}' not found.")
        sys.exit(1)

    with open(args.config, "r") as f:
        cfg = yaml.safe_load(f)

    raw_dir = cfg["paths"]["raw_dir"]
    output_dir = cfg["paths"]["processed_dir"]
    labeled_subdirs = cfg["dataset"].get("labeled_subdirs", ["tier1", "tier3", "hold", "test"])
    crop_size = tuple(cfg["preprocessing"]["crop_size"])
    padding = cfg["preprocessing"]["padding"]
    min_size = cfg["preprocessing"]["min_crop_size"]
    splits = (
        cfg["preprocessing"]["train_ratio"],
        cfg["preprocessing"]["val_ratio"],
        cfg["preprocessing"]["test_ratio"]
    )
    seed = cfg["preprocessing"]["seed"]

    print("==================================================")
    print("   xBD Multi-Tier Dataset Preprocessing MVP       ")
    print("==================================================")
    print(f"  Raw Dataset Directory:    {raw_dir}")
    print(f"  Target Subdirectories:    {labeled_subdirs}")
    print(f"  Processed Output Dir:     {output_dir}")
    print(f"  Building Crop Size:       {crop_size}")
    print(f"  Bounding Box Padding:     {padding} px")
    print(f"  Min Polygon Dimension:    {min_size} px")
    print(f"  Train/Val/Test Ratios:    {splits}")
    if args.subset_manifest:
        print(f"  SUBSET MANIFEST:          {args.subset_manifest}")
    if args.limit:
        print(f"  LIMIT MODE ENABLED:       Max {args.limit} image pairs")
    if args.validate_only:
        print("  VALIDATE-ONLY MODE:       Inspection active (no image writes)")
    print("==================================================")

    stats = process_xbd_dataset(
        raw_dir=raw_dir,
        output_dir=output_dir,
        labeled_subdirs=labeled_subdirs,
        crop_size=crop_size,
        padding=padding,
        min_crop_size=min_size,
        splits=splits,
        seed=seed,
        limit=args.limit,
        subset_manifest=args.subset_manifest,
        validate_only=args.validate_only
    )

    if stats.get("status") == "error":
        print(f"\n[PREPROCESSING FAILED] {stats.get('message')}")
        sys.exit(1)
    elif stats.get("status") == "empty":
        print("\n[PREPROCESSING FAILED] No valid building annotations processed.")
        print(f"  Scanned Directories:   {stats.get('scanned_subdirs', [])}")
        print(f"  Image Pairs Found:     {stats.get('image_pairs_found', 0)}")
        print(f"  Skipped Breakdown:     {stats.get('skipped', {})}")
        sys.exit(1)
    elif stats.get("status") == "validated":
        print("\n[SUCCESS] Dataset Validation Complete!")
        print(f"  Scanned Subdirectories:   {stats.get('scanned_subdirs')}")
        print(f"  Total Image Pairs Found:  {stats.get('image_pairs_found')}")
        print(f"  Image Pairs Validated:    {stats.get('pairs_validated')}")
        print(f"  Valid Pairs with Buildings: {stats.get('valid_image_pairs')}")
        print(f"  Estimated Valid Buildings:{stats.get('estimated_buildings')}")
        print(f"  Skipped Breakdown:        {stats.get('skipped')}")
        sys.exit(0)

    print("\n[SUCCESS] Preprocessing completed successfully!")
    print(f"  Scanned Subdirectories:   {stats.get('scanned_subdirs')}")
    print(f"  Image Pairs Discovered:   {stats.get('image_pairs_found')}")
    print(f"  Image Pairs Processed:    {stats.get('image_pairs_processed')}")
    print(f"  Unique Image Groups:      {stats.get('unique_image_groups')}")
    print(f"  Total Manifest Samples:   {stats.get('samples')}")
    print(f"  New Crops Generated:      {stats.get('new_crops_generated')}")
    print(f"  Existing Crops Skipped:   {stats.get('existing_crops_skipped')}")
    print(f"  Train Split:              {stats.get('train')} crops")
    print(f"  Validation Split:         {stats.get('val')} crops")
    print(f"  Test Split:               {stats.get('test')} crops")
    print(f"  Skipped Annotations:      {stats.get('skipped')}")

if __name__ == "__main__":
    main()
