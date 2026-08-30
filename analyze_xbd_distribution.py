"""
Script to analyze the complete xBD dataset annotation distribution,
tier breakdown, and image-pair class presence.
"""

import os
import glob
import json
from collections import Counter, defaultdict

SUBDIRS = ["tier1", "tier3", "hold", "test"]
RAW_DIR = "data/raw/xBD"
OUTPUT_JSON = "outputs/xbd_distribution.json"

DAMAGE_CLASSES = ["no-damage", "minor-damage", "major-damage", "destroyed"]

def main():
    print("==================================================")
    print("     Full xBD Dataset Distribution Analysis       ")
    print("==================================================")
    print(f"  Raw Dataset Directory: {RAW_DIR}")
    print(f"  Subdirectories:        {SUBDIRS}\n")

    overall_counts = Counter()
    tier_counts = {sd: Counter() for sd in SUBDIRS}
    
    # Image Pair Class Presence Tracking
    total_image_pairs = 0
    pair_classes_present = defaultdict(set) # base_name -> set of damage classes
    pair_tier_map = {}

    json_files_found = 0
    malformed_jsons = 0
    missing_pair_files = 0

    for subdir in SUBDIRS:
        tier_dir = os.path.join(RAW_DIR, subdir)
        labels_dir = os.path.join(tier_dir, "labels")
        images_dir = os.path.join(tier_dir, "images")

        if not (os.path.exists(labels_dir) and os.path.exists(images_dir)):
            print(f"[WARNING] Subdirectory {subdir} missing images or labels directory.")
            continue

        post_json_files = glob.glob(os.path.join(labels_dir, "*_post_disaster.json"))
        json_files_found += len(post_json_files)

        for post_json_path in post_json_files:
            base_name = os.path.basename(post_json_path).replace("_post_disaster.json", "")
            pre_json_path = os.path.join(labels_dir, f"{base_name}_pre_disaster.json")
            pre_img_path = os.path.join(images_dir, f"{base_name}_pre_disaster.png")
            post_img_path = os.path.join(images_dir, f"{base_name}_post_disaster.png")

            if not (os.path.exists(pre_json_path) and os.path.exists(pre_img_path) and os.path.exists(post_img_path)):
                missing_pair_files += 1
                continue

            total_image_pairs += 1
            pair_key = f"{subdir}_{base_name}"
            pair_tier_map[pair_key] = subdir

            try:
                with open(post_json_path, 'r') as f:
                    data = json.load(f)

                buildings = data.get("features", {}).get("xy", [])
                if not buildings:
                    overall_counts["empty_annotation_files"] += 1

                for b in buildings:
                    props = b.get("properties", {})
                    subtype = props.get("subtype", "missing_key").lower()

                    if subtype in DAMAGE_CLASSES:
                        overall_counts[subtype] += 1
                        tier_counts[subdir][subtype] += 1
                        pair_classes_present[pair_key].add(subtype)
                    elif subtype == "un-classified":
                        overall_counts["un-classified"] += 1
                        tier_counts[subdir]["un-classified"] += 1
                    else:
                        overall_counts["invalid_unknown"] += 1
                        tier_counts[subdir]["invalid_unknown"] += 1

            except Exception:
                malformed_jsons += 1

    valid_annotations = sum(overall_counts[c] for c in DAMAGE_CLASSES)
    total_annotations = valid_annotations + overall_counts["un-classified"] + overall_counts["invalid_unknown"]

    print("==================================================")
    print("          FULL xBD CLASS DISTRIBUTION             ")
    print("==================================================")
    print(f"{'Class':<20} {'Count':<12} {'Percentage':<12}")
    print("--------------------------------------------------")
    for c in DAMAGE_CLASSES:
        cnt = overall_counts[c]
        pct = (cnt / valid_annotations * 100) if valid_annotations > 0 else 0
        print(f"{c:<20} {cnt:<12} {pct:.2f}%")
    print("--------------------------------------------------")
    print(f"{'un-classified':<20} {overall_counts['un-classified']:<12} N/A")
    print(f"{'invalid/unknown':<20} {overall_counts['invalid_unknown']:<12} N/A")
    print("--------------------------------------------------")
    print(f"{'Total Valid':<20} {valid_annotations:<12} 100.00%")
    print(f"{'Total Annotations':<20} {total_annotations:<12}")
    print("==================================================\n")

    # Image Pair Presence Counts
    pairs_with_class = {c: 0 for c in DAMAGE_CLASSES}
    pairs_multi_class = 0

    for pair_key, classes_set in pair_classes_present.items():
        for c in classes_set:
            pairs_with_class[c] += 1
        if len(classes_set) > 1:
            pairs_multi_class += 1

    print("==================================================")
    print("          IMAGE-PAIR CLASS DISTRIBUTION           ")
    print("==================================================")
    print(f"Total Image Pairs: {total_image_pairs}")
    for c in DAMAGE_CLASSES:
        print(f"  Pairs with at least one {c:<14}: {pairs_with_class[c]:<6} ({pairs_with_class[c]/total_image_pairs*100:.2f}%)")
    print(f"  Pairs with multiple damage classes : {pairs_multi_class:<6} ({pairs_multi_class/total_image_pairs*100:.2f}%)")
    print("==================================================\n")

    print("==================================================")
    print("            DISTRIBUTION BY TIER                  ")
    print("==================================================")
    print(f"{'Class':<18} " + "".join([f"{sd:>12}" for sd in SUBDIRS]))
    print("--------------------------------------------------")
    for c in DAMAGE_CLASSES + ["un-classified"]:
        row = f"{c:<18} " + "".join([f"{tier_counts[sd][c]:>12}" for sd in SUBDIRS])
        print(row)
    print("==================================================\n")

    # Construct JSON Output
    results = {
        "dataset_summary": {
            "json_files_found": json_files_found,
            "total_image_pairs": total_image_pairs,
            "missing_pair_files": missing_pair_files,
            "malformed_jsons": malformed_jsons,
            "total_annotations_examined": total_annotations,
            "total_valid_annotations": valid_annotations
        },
        "four_class_distribution": {
            c: {
                "count": overall_counts[c],
                "percentage": round((overall_counts[c] / valid_annotations * 100), 2) if valid_annotations > 0 else 0
            } for c in DAMAGE_CLASSES
        },
        "unmapped_annotations": {
            "un-classified": overall_counts["un-classified"],
            "invalid_unknown": overall_counts["invalid_unknown"]
        },
        "image_pair_distribution": {
            "total_pairs": total_image_pairs,
            "pairs_with_class": pairs_with_class,
            "pairs_multi_class": pairs_multi_class
        },
        "tier_distribution": {
            sd: {c: tier_counts[sd][c] for c in DAMAGE_CLASSES + ["un-classified"]} for sd in SUBDIRS
        }
    }

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)

    print(f"[SUCCESS] Saved full distribution results to '{OUTPUT_JSON}'.")

if __name__ == "__main__":
    main()
