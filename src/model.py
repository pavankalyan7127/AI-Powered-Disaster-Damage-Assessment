"""
Siamese Model Architecture for Pre/Post Disaster Building Damage Assessment.
"""

import torch
import torch.nn as nn
from torchvision.models import resnet50, ResNet50_Weights

class SiameseDamageClassifier(nn.Module):
    def __init__(self, num_classes: int = 4, dropout: float = 0.3):
        super().__init__()
        # Shared feature extractor backbone (ResNet50)
        backbone = resnet50(weights=ResNet50_Weights.DEFAULT)
        # Exclude original FC layer and average pool
        self.encoder = nn.Sequential(*list(backbone.children())[:-2]) # Output shape: (B, 2048, H/32, W/32)
        self.adaptive_pool = nn.AdaptiveAvgPool2d((1, 1))
        
        # Combined Feature Dimension: Pre (2048) + Post (2048) + Difference (2048) = 6144
        feature_dim = 2048 * 3

        # Multi-class Classification Head
        self.classifier = nn.Sequential(
            nn.Linear(feature_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, num_classes)
        )

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        feat_map = self.encoder(x)
        pooled = self.adaptive_pool(feat_map)
        return torch.flatten(pooled, 1)

    def forward(self, pre_img: torch.Tensor, post_img: torch.Tensor) -> torch.Tensor:
        feat_pre = self.extract_features(pre_img)   # (B, 2048)
        feat_post = self.extract_features(post_img) # (B, 2048)
        feat_diff = torch.abs(feat_post - feat_pre)  # (B, 2048)
        
        # Concatenate pre-disaster, post-disaster, and difference vectors
        combined = torch.cat([feat_pre, feat_post, feat_diff], dim=1) # (B, 6144)
        return self.classifier(combined)
