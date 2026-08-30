"""
Evaluation script for testing trained Siamese Building Damage Assessment Classifier on test set.
"""

import os
import sys
import json
import yaml
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from src.dataset import BuildingDamageDataset
from src.model import SiameseDamageClassifier

CLASS_NAMES = {
    0: "no-damage",
    1: "minor-damage",
    2: "major-damage",
    3: "destroyed"
}

def main():
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        print(f"[ERROR] Configuration file '{config_path}' not found.")
        sys.exit(1)

    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    processed_dir = cfg["paths"]["processed_dir"]
    test_manifest = os.path.join(processed_dir, "test_manifest.json")
    checkpoint_path = cfg["paths"]["checkpoint_file"]
    output_dir = cfg["paths"]["output_dir"]

    # Error handling for missing required artifacts
    if not os.path.exists(test_manifest):
        print(f"\n[ERROR] Test dataset manifest not found at: '{test_manifest}'")
        print("Please ensure dataset preprocessing has been executed and generated 'test_manifest.json'.")
        sys.exit(1)

    if not os.path.exists(checkpoint_path):
        print(f"\n[ERROR] Model checkpoint file not found at: '{checkpoint_path}'")
        print("Please ensure a model has been trained and saved before testing.")
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("==================================================")
    print("       Disaster Damage Assessment Testing         ")
    print("==================================================")
    print(f"  Device:               {device}")
    print(f"  Test Manifest Path:   {test_manifest}")
    print(f"  Model Checkpoint:     {checkpoint_path}")
    print("==================================================")

    # Load Test PyTorch Dataset
    try:
        test_dataset = BuildingDamageDataset(test_manifest)
    except Exception as e:
        print(f"[ERROR] Failed to load test dataset: {e}")
        sys.exit(1)

    if len(test_dataset) == 0:
        print("[ERROR] Test dataset contains 0 samples. Cannot perform evaluation.")
        sys.exit(1)

    test_loader = DataLoader(
        test_dataset,
        batch_size=cfg["training"]["batch_size"],
        shuffle=False,
        num_workers=cfg["training"]["num_workers"]
    )

    # Initialize Model Architecture
    try:
        model = SiameseDamageClassifier(
            num_classes=cfg["model"]["num_classes"],
            dropout=cfg["model"]["dropout"]
        ).to(device)
    except Exception as e:
        print(f"[ERROR] Failed to instantiate SiameseDamageClassifier model: {e}")
        sys.exit(1)

    # Restore Checkpoint
    try:
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        print(f"[INFO] Successfully loaded model checkpoint from epoch {checkpoint.get('epoch', 'N/A')}.")
    except Exception as e:
        print(f"[ERROR] Failed to load or parse checkpoint '{checkpoint_path}': {e}")
        sys.exit(1)

    criterion = nn.CrossEntropyLoss()
    model.eval()

    running_loss = 0.0
    all_preds = []
    all_targets = []

    # Evaluation Loop
    with torch.no_grad():
        for pre_img, post_img, labels in tqdm(test_loader, desc="Testing Inference", leave=False):
            pre_img = pre_img.to(device)
            post_img = post_img.to(device)
            labels = labels.to(device)

            outputs = model(pre_img, post_img)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * pre_img.size(0)
            _, preds = torch.max(outputs, 1)

            all_preds.extend(preds.cpu().numpy().tolist())
            all_targets.extend(labels.cpu().numpy().tolist())

    total_samples = len(all_targets)
    test_loss = running_loss / total_samples

    correct_total = sum(1 for p, t in zip(all_preds, all_targets) if p == t)
    incorrect_total = total_samples - correct_total
    overall_accuracy = (correct_total / total_samples) * 100

    # Calculate Per-Class Performance
    num_classes = cfg["model"]["num_classes"]
    class_total = [0] * num_classes
    class_correct = [0] * num_classes

    # Build Confusion Matrix (rows: actual, cols: predicted)
    confusion_matrix = [[0] * num_classes for _ in range(num_classes)]

    for p, t in zip(all_preds, all_targets):
        class_total[t] += 1
        if p == t:
            class_correct[t] += 1
        confusion_matrix[t][p] += 1

    print("\n==================================================")
    print(f"  Test Samples:         {total_samples}")
    print(f"  Test Loss:            {test_loss:.4f}")
    print(f"  Test Accuracy:        {overall_accuracy:.2f}%")
    print(f"  Correct Predictions:   {correct_total}")
    print(f"  Incorrect Predictions: {incorrect_total}")
    print("--------------------------------------------------")
    print("  Class Performance:")
    for c_id in range(num_classes):
        c_name = CLASS_NAMES.get(c_id, f"class_{c_id}")
        tot = class_total[c_id]
        corr = class_correct[c_id]
        acc = (corr / tot * 100) if tot > 0 else 0.0
        print(f"    {c_name:<15}: {corr}/{tot} correct ({acc:.2f}%)")

    print("\n  Confusion Matrix (Rows: Actual, Cols: Predicted):")
    header = "             " + "".join([f"{CLASS_NAMES[i]:>15}" for i in range(num_classes)])
    print(header)
    for i in range(num_classes):
        row_str = f"  {CLASS_NAMES[i]:<11}: " + "".join([f"{confusion_matrix[i][j]:>15}" for j in range(num_classes)])
        print(row_str)
    print("==================================================")

    # Save results summary to JSON file
    results_summary = {
        "test_samples": total_samples,
        "test_loss": test_loss,
        "test_accuracy": overall_accuracy,
        "correct_predictions": correct_total,
        "incorrect_predictions": incorrect_total,
        "per_class_performance": {
            CLASS_NAMES[i]: {
                "total": class_total[i],
                "correct": class_correct[i],
                "accuracy": (class_correct[i] / class_total[i] * 100) if class_total[i] > 0 else 0.0
            } for i in range(num_classes)
        },
        "confusion_matrix": {
            "classes": [CLASS_NAMES[i] for i in range(num_classes)],
            "matrix": confusion_matrix
        }
    }

    os.makedirs(output_dir, exist_ok=True)
    results_json_path = os.path.join(output_dir, "test_results.json")
    with open(results_json_path, "w") as f:
        json.dump(results_summary, f, indent=2)

    print(f"\n[SUCCESS] Test results saved to '{results_json_path}'!")
    print("==================================================")
    print("Testing completed successfully!")
    print("==================================================")

if __name__ == "__main__":
    main()
