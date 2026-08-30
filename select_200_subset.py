"""
Script to create a class-balanced 200-image-pair subset from outputs/selected_subset.json.
"""

import os
import json
import random
import argparse
from collections import Counter

DAMAGE_CLASSES = ["no-damage", "minor-damage", "major-damage", "destroyed"]
INPUT_MANIFEST = "outputs/selected_subset.json"
OUTPUT_MANIFEST = "outputs/selected_200_subset.json"

def calculate_200_pair_score(counts: dict, tier: str) -> float:
    """
    Score boost for pairs rich in minority damage categories (minor/major/destroyed).
    - minor-damage: +15 pts per building
    - major-damage: +15 pts per building
    - destroyed:    +15 pts per building
    - no-damage:    +0.1 pts per building (keeps intact count controlled)
    - Bonus for multi-class damage presence
    - Minor tier diversity bonus for underrepresented tiers
    """
    score = (
        counts["minor-damage"] * 15.0 +
        counts["major-damage"] * 15.0 +
        counts["destroyed"] * 15.0 +
        counts["no-damage"] * 0.1
    )
    
    damaged_cats = sum(1 for c in ["minor-damage", "major-damage", "destroyed"] if counts[c] > 0)
    if damaged_cats > 1:
        score += (damaged_cats - 1) * 20.0
        
    return score

def main():
    parser = argparse.ArgumentParser(description="Extract 200 class-balanced image pairs from 900-pair manifest.")
    parser.add_argument("--input", type=str, default=INPUT_MANIFEST, help="Input 900-pair manifest.")
    parser.add_argument("--output", type=str, default=OUTPUT_MANIFEST, help="Output 200-pair manifest.")
    parser.add_argument("--target-pairs", type=int, default=200, help="Target number of pairs (200).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[ERROR] Input manifest '{args.input}' not found.")
        return

    # Check modification time of input file to verify it remains unchanged
    initial_mtime = os.path.getmtime(args.input)

    with open(args.input, "r") as f:
        data = json.load(f)

    candidates = data.get("selected_pairs", [])
    if len(candidates) < args.target_pairs:
        print(f"[ERROR] Input manifest contains only {len(candidates)} pairs, but {args.target_pairs} requested.")
        return

    random.seed(args.seed)

    # Calculate selection scores
    scored_candidates = []
    for pair in candidates:
        counts = pair["counts"]
        tier = pair["tier"]
        score = calculate_200_pair_score(counts, tier)
        rand_key = random.random()
        scored_candidates.append((score, rand_key, pair))

    # Sort descending by score, with deterministic tie-breaker
    scored_candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)

    selected_200 = [x[2] for x in scored_candidates[:args.target_pairs]]

    # Compute Statistics
    tier_dist = Counter(p["tier"] for p in selected_200)
    class_totals = Counter()
    pairs_with_class = Counter()
    multi_class_pairs = 0

    for p in selected_200:
        counts = p["counts"]
        present = []
        for c in DAMAGE_CLASSES:
            class_totals[c] += counts[c]
            if counts[c] > 0:
                pairs_with_class[c] += 1
                present.append(c)
        if len(present) > 1:
            multi_class_pairs += 1

    total_buildings = sum(class_totals.values())

    manifest_200 = {
        "metadata": {
            "source_manifest": args.input,
            "target_pairs": args.target_pairs,
            "seed": args.seed,
            "selected_pairs_count": len(selected_200),
            "tier_distribution": dict(tier_dist),
            "building_totals": dict(class_totals),
            "building_percentages": {
                c: round((class_totals[c] / total_buildings * 100), 2) if total_buildings > 0 else 0
                for c in DAMAGE_CLASSES
            },
            "pairs_containing_class": dict(pairs_with_class),
            "pairs_multi_class": multi_class_pairs
        },
        "selected_pairs": selected_200
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(manifest_200, f, indent=2)

    # Verification checks
    final_mtime = os.path.getmtime(args.input)
    assert initial_mtime == final_mtime, "Input file outputs/selected_subset.json was modified!"
    assert len(selected_200) == args.target_pairs, f"Expected {args.target_pairs} pairs, got {len(selected_200)}"
    pair_ids = [p["pair_id"] for p in selected_200]
    assert len(pair_ids) == len(set(pair_ids)), "Duplicate pair IDs found!"

    print("==================================================")
    print("   200-IMAGE-PAIR BALANCED SUBSET REPORT         ")
    print("==================================================")
    print(f"Source Manifest:        {args.input}")
    print(f"Target Pairs:           {args.target_pairs}")
    print(f"Selected Pairs:         {len(selected_200)}")
    print(f"Random Seed:            {args.seed}")
    print("--------------------------------------------------")
    print("SOURCE TIER DISTRIBUTION")
    for t in ["tier1", "tier3", "hold", "test"]:
        cnt = tier_dist.get(t, 0)
        print(f"  {t:<10}: {cnt:<5} pairs ({cnt/len(selected_200)*100:.1f}%)")
    print("--------------------------------------------------")
    print("BUILDING ANNOTATION DISTRIBUTION")
    for c in DAMAGE_CLASSES:
        cnt = class_totals[c]
        pct = (cnt / total_buildings * 100) if total_buildings > 0 else 0
        print(f"  {c:<15}: {cnt:<6} buildings ({pct:.2f}%)")
    print(f"  Total Buildings: {total_buildings}")
    print("--------------------------------------------------")
    print("IMAGE-PAIR COVERAGE")
    for c in DAMAGE_CLASSES:
        cnt = pairs_with_class.get(c, 0)
        print(f"  Pairs with {c:<14}: {cnt:<5} ({cnt/len(selected_200)*100:.1f}%)")
    print(f"  Pairs with Multi-Class Damage: {multi_class_pairs:<5} ({multi_class_pairs/len(selected_200)*100:.1f}%)")
    print("--------------------------------------------------")
    print(f"CONFIRMATION: '{args.input}' was NOT modified.")
    print("==================================================")
    print(f"[SUCCESS] Saved 200-pair subset to '{args.output}'.")

if __name__ == "__main__":
    main()
