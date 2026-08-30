# Disaster Damage Assessment — Hackathon MVP

An AI-powered computer vision system that analyzes paired pre-disaster and post-disaster satellite imagery from the xView2/xBD dataset to classify individual building damage severity.

## Overview & Architecture
- **Task**: 4-class building damage classification (`0=no-damage`, `1=minor-damage`, `2=major-damage`, `3=destroyed`).
- **Model**: Siamese ResNet50 Architecture. Features extracted from pre-disaster imagery, post-disaster imagery, and their absolute element-wise difference are combined before passing into a classification head.
- **Data Pipeline**: Crops bounding boxes of building polygons extracted from WKT annotations in xBD JSON files (`features['xy']`). Groups crops by original image pair prefix to prevent data leakage across `train/val/test` splits.

---

## Directory Setup
Place the uncompressed xBD dataset in `data/raw/xBD/` matching the multi-tier structure:
```
data/
└── raw/
    └── xBD/
        ├── tier1/
        │   ├── images/
        │   ├── labels/
        │   └── masks/
        ├── tier3/
        │   ├── images/
        │   ├── labels/
        │   └── masks/
        ├── hold/
        │   ├── images/
        │   ├── labels/
        │   └── masks/
        └── test/
            ├── images/
            ├── labels/
            └── masks/
```

---

## Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Offline Dataset Preprocessing
Scans labeled subdirectories (`tier1`, `tier3`, `hold`, `test`), pairs pre/post images and annotations, extracts building crops with bounding-box padding, resizes them to `128x128`, performs group-level splitting (no image pair leakage), and outputs manifests:
```bash
python preprocess.py --config config.yaml
```

Processed data will be saved to `data/processed/` along with `train_manifest.json`, `val_manifest.json`, and `test_manifest.json`.

### 3. Model Training
Runs local PyTorch model training (automatically using CUDA if available, CPU otherwise):
```bash
python train.py
```

The best model checkpoint based on validation loss will be automatically saved to `outputs/best_siamese_model.pth`.
