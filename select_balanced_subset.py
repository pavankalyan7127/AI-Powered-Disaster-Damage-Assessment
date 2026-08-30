"""
Reproducible, Class-Aware Image-Pair Selector for xBD Dataset.
"""

import os
import glob
import json
import random
import argparse
from typing import Dict, Any, List
from collections import Counter, defaultdict

RAW_DIR = "data/raw/xBD"
SUBDIRS = ["tier1", "tier3", "hold", "test"]
DAMAGE_CLASSES = ["no-damage", "minor-damage", "major-damage", "destroyed"]

def calculate_pair_score(counts: Dict[str, int], tier: str) -> float:
    """
    Scoring formula prioritizing damaged buildings, multi-class presence, and tier1.
    - minor-damage: 10.0 pts per building
    - major-damage: 12.0 pts per building
    - destroyed: 12.0 pts per building
    - no-damage: 0.1 pts per building (low priority so intact-only scenes rank lower)
    - Bonus for containing multiple damage categories (+15.0 pts per additional damaged category)
    - Bonus for tier1 (+5.0 pts tier multiplier)
    """
    score = (
        counts["minor-damage"] * 10.0 +
        counts["major-damage"] * 12.0 +
        counts["destroyed"] * 12.0 +
        counts["no-damage"] * 0.1
    )

    # Multi-class diversity bonus
    damaged_categories = sum(1 for c in ["minor-damage", "major-damage", "destroyed"] if counts[c] > 0)
    if damaged_categories > 1:
        score += (damaged_categories - 1) * 15.0

    # Tier priority bonus
    if tier == "tier1":
        score += 5.0

    return score

def select_subset(
    raw_dir: str = RAW_DIR,
    subdirs: List[str] = SUBDIRS,
    target_pairs: int = 900,
    seed: int = 42
) -> Dict[str, Any]:
    random.seed(seed)
    candidate_pairs = []

    print("[1/3] Scanning candidate image pairs across xBD subdirectories...")

    for subdir in subdirs:
        tier_dir = os.path.join(raw_dir, subdir)
        labels_dir = os.path.join(tier_dir, "labels")
        images_dir = os.path.join(tier_dir, "images")

        if not (os.path.exists(labels_dir) and os.path.exists(images_dir)):
            continue

        post_json_files = glob.glob(os.path.join(labels_dir, "*_post_disaster.json"))

        for post_json_path in post_json_files:
            base_name = os.path.basename(post_json_path).replace("_post_disaster.json", "")
            pre_json_path = os.path.join(labels_dir, f"{base_name}_pre_disaster.json")
            pre_img_path = os.path.join(images_dir, f"{base_name}_pre_disaster.png")
            post_img_path = os.path.join(images_dir, f"{base_name}_post_disaster.png")

            if not (os.path.exists(pre_json_path) and os.path.exists(pre_img_path) and os.path.exists(post_img_path)):
                continue

            try:
                with open(post_json_path, 'r') as f:
                    data = json.load(f)

                counts = {c: 0 for c in DAMAGE_CLASSES}
                buildings = data.get("features", {}).get("xy", [])

                for b in buildings:
                    subtype = b.get("properties", {}).get("subtype", "").lower()
                    if subtype in counts:
                        counts[subtype] += 1

                total_valid = sum(counts.values())
                if total_valid == 0:
                    continue

                pair_id = f"{subdir}_{base_name}"
                score = calculate_pair_score(counts, subdir)

                candidate_pairs.append({
                    "pair_id": pair_id,
                    "tier": subdir,
                    "base_name": base_name,
                    "pre_image": pre_img_path,
                    "post_image": post_img_path,
                    "pre_json": pre_json_path,
                    "post_json": post_json_path,
                    "counts": counts,
                    "total_valid": total_valid,
                    "score": score
                })
            except Exception:
                continue

    total_candidates = len(candidate_pairs)
    print(f"  Discovered {total_candidates} candidate image pairs.")

    print("[2/3] Ranking and selecting class-aware subset...")

    for pair in candidate_pairs:
        pair["rand_key"] = random.random()

    candidate_pairs.sort(key=lambda x: (x["score"], x["rand_key"]), reverse=True)

    selected_pairs = candidate_pairs[:min(target_pairs, total_candidates)]

    # Aggregate Statistics
    tier_dist = Counter(p["tier"] for p in selected_pairs)
    class_totals = Counter()
    pairs_with_class = Counter()
    multi_class_pairs = 0

    for pair in selected_pairs:
        counts = pair["counts"]
        present = []
        for c in DAMAGE_CLASSES:
            class_totals[c] += counts[c]
            if counts[c] > 0:
                pairs_with_class[c] += 1
                present.append(c)
        if len(present) > 1:
            multi_class_pairs += 1

    total_buildings = sum(class_totals.values())

    subset_manifest = {
        "metadata": {
            "seed": seed,
            "target_pairs": target_pairs,
            "selected_pairs_count": len(selected_pairs),
            "total_candidate_pairs": total_candidates,
            "tier_distribution": dict(tier_dist),
            "building_totals": dict(class_totals),
            "building_percentages": {
                c: round((class_totals[c] / total_buildings * 100), 2) if total_buildings > 0 else 0
                for c in DAMAGE_CLASSES
            },
            "pairs_containing_class": dict(pairs_with_class),
            "pairs_multi_class": multi_class_pairs
        },
        "selected_pairs": [
            {
                "pair_id": p["pair_id"],
                "tier": p["tier"],
                "base_name": p["base_name"],
                "pre_image": p["pre_image"],
                "post_image": p["post_image"],
                "pre_json": p["pre_json"],
                "post_json": p["post_json"],
                "counts": p["counts"],
                "score": round(p["score"], 2)
            }
            for p in selected_pairs
        ]
    }

    return subset_manifest

def main():
    parser = argparse.ArgumentParser(description="Select class-aware image-pair subset from xBD.")
    parser.add_argument("--target-pairs", type=int, default=900, help="Target number of image pairs to select.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--output", type=str, default="outputs/selected_subset.json", help="Output JSON path.")
    args = parser.parse_args()

    manifest = select_subset(
        target_pairs=args.target_pairs,
        seed=args.seed
    )

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(manifest, f, indent=2)

    meta = manifest["metadata"]
    b_totals = meta["building_totals"]
    b_pcts = meta["building_percentages"]
    p_coverage = meta["pairs_containing_class"]

    print("\n==================================================")
    print("      xBD CLASS-AWARE SUBSET SELECTION REPORT     ")
    print("==================================================")
    print(f"Total Candidate Pairs:  {meta['total_candidate_pairs']}")
    print(f"Target Pairs:           {meta['target_pairs']}")
    print(f"Selected Pairs:         {meta['selected_pairs_count']}")
    print(f"Random Seed:            {meta['seed']}")
    print("--------------------------------------------------")
    print("SOURCE TIER DISTRIBUTION")
    for t, cnt in meta['tier_distribution'].items():
        print(f"  {t:<10}: {cnt:<5} pairs ({cnt/meta['selected_pairs_count']*100:.1f}%)")
    print("--------------------------------------------------")
    print("BUILDING ANNOTATION DISTRIBUTION")
    for c in DAMAGE_CLASSES:
        print(f"  {c:<15}: {b_totals[c]:<6} ({b_pcts[c]:.2f}%)")
    print(f"  Total Buildings: {sum(b_totals.values())}")
    print("--------------------------------------------------")
    print("IMAGE-PAIR COVERAGE")
    for c in DAMAGE_CLASSES:
        print(f"  Pairs with {c:<14}: {p_coverage.get(c, 0):<5} ({p_coverage.get(c, 0)/meta['selected_pairs_count']*100:.1f}%)")
    print(f"  Pairs with Multi-Class Damage: {meta['pairs_multi_class']:<5} ({meta['pairs_multi_class']/meta['selected_pairs_count']*100:.1f}%)")
    print("==================================================")
    print(f"[SUCCESS] Saved selected subset manifest to '{args.output}'.")

if __name__ == "__main__":
    main()
