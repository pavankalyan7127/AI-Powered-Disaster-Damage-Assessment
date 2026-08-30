"""
Training script for Siamese Building Damage Assessment Classifier MVP.
"""

import os
import sys
import yaml
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from src.dataset import BuildingDamageDataset
from src.model import SiameseDamageClassifier

def train_one_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for pre_img, post_img, labels in tqdm(dataloader, desc="Training Batch", leave=False):
        pre_img = pre_img.to(device)
        post_img = post_img.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(pre_img, post_img)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * pre_img.size(0)
        _, preds = torch.max(outputs, 1)
        correct += torch.sum(preds == labels.data).item()
        total += labels.size(0)

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc

def evaluate(model, dataloader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for pre_img, post_img, labels in tqdm(dataloader, desc="Validation Batch", leave=False):
            pre_img = pre_img.to(device)
            post_img = post_img.to(device)
            labels = labels.to(device)

            outputs = model(pre_img, post_img)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * pre_img.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels.data).item()
            total += labels.size(0)

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc

def main():
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        print(f"[ERROR] Config file '{config_path}' not found.")
        sys.exit(1)

    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    processed_dir = cfg["paths"]["processed_dir"]
    train_manifest = os.path.join(processed_dir, "train_manifest.json")
    val_manifest = os.path.join(processed_dir, "val_manifest.json")
    checkpoint_path = cfg["paths"]["checkpoint_file"]

    if not (os.path.exists(train_manifest) and os.path.exists(val_manifest)):
        print("\n[ERROR] Preprocessed data manifests not found.")
        print(f"  Missing: {train_manifest} or {val_manifest}")
        print("Please run data preprocessing first:")
        print("  python preprocess.py --config config.yaml")
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("==================================================")
    print("   Disaster Damage Assessment Model Training     ")
    print("==================================================")
    print(f"  Device:               {device}")
    print(f"  Batch Size:           {cfg['training']['batch_size']}")
    print(f"  Total Target Epochs:  {cfg['training']['epochs']}")
    print(f"  Learning Rate:        {cfg['training']['learning_rate']}")
    print(f"  Model Checkpoint Path: {checkpoint_path}")
    print("==================================================")

    # Load PyTorch Datasets
    try:
        train_dataset = BuildingDamageDataset(train_manifest)
        val_dataset = BuildingDamageDataset(val_manifest)
    except Exception as e:
        print(f"[ERROR] Failed to load dataset: {e}")
        sys.exit(1)

    train_loader = DataLoader(
        train_dataset,
        batch_size=cfg["training"]["batch_size"],
        shuffle=True,
        num_workers=cfg["training"]["num_workers"]
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=cfg["training"]["batch_size"],
        shuffle=False,
        num_workers=cfg["training"]["num_workers"]
    )

    print(f"[INFO] Dataset loaded: {len(train_dataset)} training pairs, {len(val_dataset)} validation pairs.")

    # Initialize Model, Criterion, Optimizer
    model = SiameseDamageClassifier(
        num_classes=cfg["model"]["num_classes"],
        dropout=cfg["model"]["dropout"]
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(cfg["training"]["learning_rate"]))

    start_epoch = 1
    best_val_loss = float("inf")
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)

    # Checkpoint resumption logic
    if os.path.exists(checkpoint_path):
        try:
            checkpoint = torch.load(checkpoint_path, map_location=device)
            model.load_state_dict(checkpoint["model_state_dict"])
            if "optimizer_state_dict" in checkpoint:
                optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            saved_epoch = checkpoint.get("epoch", 0)
            start_epoch = saved_epoch + 1
            best_val_loss = checkpoint.get("val_loss", float("inf"))
            print(f"\n[INFO] Resuming training from checkpoint at epoch {saved_epoch}.")
            print(f"[INFO] Saved Validation Loss: {best_val_loss:.4f}")
            print(f"[INFO] Starting from epoch {start_epoch} (Target: {cfg['training']['epochs']}).")
        except Exception as e:
            print(f"[WARNING] Could not load checkpoint at '{checkpoint_path}': {e}")
            print("[INFO] Starting training from scratch (Epoch 1).")
    else:
        print("[INFO] No existing checkpoint found. Starting training from epoch 1.")

    total_epochs = cfg["training"]["epochs"]
    if start_epoch > total_epochs:
        print(f"\n[INFO] Model already trained for {start_epoch - 1} epochs (Target: {total_epochs}). Nothing to train.")
        return

    for epoch in range(start_epoch, total_epochs + 1):
        print(f"\n--- Epoch {epoch}/{total_epochs} ---")
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)

        print(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc * 100:.2f}%")
        print(f"  Val Loss:   {val_loss:.4f} | Val Acc:   {val_acc * 100:.2f}%")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_loss": val_loss,
                "val_acc": val_acc
            }, checkpoint_path)
            print(f"  [SAVED] Best model updated and saved to {checkpoint_path}")

    print("\n[COMPLETE] Model training completed successfully!")

if __name__ == "__main__":
    main()
