"""
Production-Ready Inference Module for Siamese Disaster Building Damage Classifier.
"""

import os
import sys
import json
import yaml
import glob
import torch
import torch.nn as nn
import numpy as np
from PIL import Image
import argparse
from typing import Dict, Any, Union, Optional, Tuple, List

from src.model import SiameseDamageClassifier

CLASS_MAPPING = {
    0: "no-damage",
    1: "minor-damage",
    2: "major-damage",
    3: "destroyed"
}

class DamageInference:
    """
    Reusable inference engine for building damage assessment using a trained Siamese model.
    Expects paired pre-disaster and post-disaster building crops (e.g. 128x128).
    """

    def __init__(
        self,
        checkpoint_path: str = "outputs/best_siamese_model.pth",
        config_path: str = "config.yaml",
        device: Optional[str] = None
    ):
        self.checkpoint_path = checkpoint_path
        self.config_path = config_path

        # Device selection: CUDA if available, fallback to CPU
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Load Configuration
        self.cfg = self._load_config()

        # Instantiate & Load Model
        self.model = self._load_model()

        # Define Normalization Constants (ImageNet Standard)
        self.mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1).to(self.device)
        self.std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1).to(self.device)
        self.target_size = tuple(self.cfg["preprocessing"].get("crop_size", [128, 128]))

    def _load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found at '{self.config_path}'.")
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def _load_model(self) -> nn.Module:
        if not os.path.exists(self.checkpoint_path):
            raise FileNotFoundError(
                f"Checkpoint file not found at '{self.checkpoint_path}'. "
                "Ensure model checkpoint is present before running inference."
            )

        num_classes = self.cfg["model"].get("num_classes", 4)
        dropout = self.cfg["model"].get("dropout", 0.3)

        try:
            model = SiameseDamageClassifier(num_classes=num_classes, dropout=dropout)
            checkpoint = torch.load(self.checkpoint_path, map_location=self.device)

            if "model_state_dict" in checkpoint:
                model.load_state_dict(checkpoint["model_state_dict"])
            else:
                model.load_state_dict(checkpoint)

            model.to(self.device)
            model.eval()
            return model
        except Exception as e:
            raise RuntimeError(f"Failed to instantiate or load checkpoint from '{self.checkpoint_path}': {e}")

    def preprocess_image(self, img_input: Union[str, Image.Image]) -> torch.Tensor:
        """
        Loads, resizes, normalizes an image and converts it to a PyTorch Tensor.
        img_input can be a file path string or a PIL Image object.
        """
        if isinstance(img_input, str):
            if not os.path.exists(img_input):
                raise FileNotFoundError(f"Image file not found at '{img_input}'.")
            try:
                img = Image.open(img_input).convert("RGB")
            except Exception as e:
                raise ValueError(f"Failed to open or decode image file '{img_input}': {e}")
        elif isinstance(img_input, Image.Image):
            img = img_input.convert("RGB")
        else:
            raise TypeError(f"Unsupported image input type: {type(img_input)}. Expected filepath str or PIL.Image.")

        # Ensure image matches target training size (128x128)
        if img.size != self.target_size:
            img = img.resize(self.target_size, Image.Resampling.BILINEAR)

        # Convert to numpy array and scale to [0, 1]
        img_np = np.array(img, dtype=np.float32) / 255.0

        # Permute HWC to CHW
        tensor = torch.from_numpy(img_np).permute(2, 0, 1).to(self.device)

        # Apply Standard ImageNet Normalization
        tensor = (tensor - self.mean) / self.std
        return tensor

    def predict_pair(
        self,
        pre_image: Union[str, Image.Image],
        post_image: Union[str, Image.Image]
    ) -> Dict[str, Any]:
        """
        Runs inference on a paired pre-disaster and post-disaster building crop.
        Returns a structured dictionary suitable for API JSON responses.
        """
        pre_tensor = self.preprocess_image(pre_image).unsqueeze(0)   # Shape: (1, 3, H, W)
        post_tensor = self.preprocess_image(post_image).unsqueeze(0) # Shape: (1, 3, H, W)

        with torch.no_grad():
            logits = self.model(pre_tensor, post_tensor)
            probs = torch.softmax(logits, dim=1).squeeze(0)

        pred_idx = int(torch.argmax(probs).item())
        confidence = float(probs[pred_idx].item())

        prob_dict = {
            CLASS_MAPPING[i]: round(float(probs[i].item()), 4)
            for i in range(len(CLASS_MAPPING))
        }

        return {
            "predicted_class": pred_idx,
            "predicted_label": CLASS_MAPPING[pred_idx],
            "confidence": round(confidence, 4),
            "probabilities": prob_dict,
            "device": str(self.device)
        }

    def predict_multiple_pairs(
        self,
        pairs: List[Tuple[Union[str, Image.Image], Union[str, Image.Image]]]
    ) -> List[Dict[str, Any]]:
        """
        Batch prediction helper for multiple pre/post building crop pairs.
        """
        results = []
        for pre_img, post_img in pairs:
            results.append(self.predict_pair(pre_img, post_img))
        return results

    def predict_directory(
        self,
        input_dir: str,
        output_path: Optional[str] = "outputs/nepal_inference_results.json"
    ) -> Dict[str, Any]:
        """
        Scans input_dir for folders containing both pre.png and post.png, runs batch inference,
        and creates an aggregate disaster assessment summary dictionary.
        """
        if not os.path.exists(input_dir):
            raise FileNotFoundError(f"Input directory not found at '{input_dir}'.")

        # Discover all subdirectories containing pre.png and post.png
        building_folders = []
        for root, dirs, files in os.walk(input_dir):
            if "pre.png" in files and "post.png" in files:
                building_folders.append(root)

        building_folders.sort()
        total_buildings = len(building_folders)

        results_list = []
        damage_counts = {label: 0 for label in CLASS_MAPPING.values()}
        confidence_sum = 0.0
        processed_count = 0
        failed_count = 0

        for folder in building_folders:
            folder_name = os.path.basename(folder)
            pre_path = os.path.join(folder, "pre.png")
            post_path = os.path.join(folder, "post.png")
            meta_path = os.path.join(folder, "metadata.json")

            b_id = folder_name
            meta_data = {}
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r") as mf:
                        meta_data = json.load(mf)
                    b_id = meta_data.get("building_id", folder_name)
                except Exception:
                    pass

            try:
                pair_res = self.predict_pair(pre_path, post_path)
                pred_label = pair_res["predicted_label"]
                conf = pair_res["confidence"]

                damage_counts[pred_label] += 1
                confidence_sum += conf
                processed_count += 1

                b_entry = {
                    "building_id": b_id,
                    "folder": folder_name,
                    "pre_image": pre_path,
                    "post_image": post_path,
                    "predicted_class": pair_res["predicted_class"],
                    "predicted_label": pred_label,
                    "confidence": conf,
                    "probabilities": pair_res["probabilities"]
                }
                if meta_data:
                    b_entry["metadata"] = meta_data

                results_list.append(b_entry)

            except Exception as e:
                failed_count += 1
                results_list.append({
                    "building_id": b_id,
                    "folder": folder_name,
                    "status": "error",
                    "error": str(e)
                })

        avg_confidence = round((confidence_sum / processed_count * 100), 2) if processed_count > 0 else 0.0
        percentages = {
            label: round((damage_counts[label] / processed_count * 100), 2) if processed_count > 0 else 0.0
            for label in CLASS_MAPPING.values()
        }

        summary = {
            "status": "success",
            "disaster": "Nepal Flood/Landslide 2026",
            "device": str(self.device),
            "model_checkpoint": self.checkpoint_path,
            "total_buildings": total_buildings,
            "processed_buildings": processed_count,
            "failed_buildings": failed_count,
            "damage_distribution": damage_counts,
            "percentages": percentages,
            "average_confidence": avg_confidence,
            "buildings": results_list
        }

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(summary, f, indent=2)

        return summary


def main():
    parser = argparse.ArgumentParser(description="Run inference on paired pre/post disaster building crop images or directories.")
    parser.add_argument("--pre", type=str, default=None, help="Path to pre-disaster building crop image.")
    parser.add_argument("--post", type=str, default=None, help="Path to post-disaster building crop image.")
    parser.add_argument("--input-dir", type=str, default=None, help="Input directory containing building crop folders (each with pre.png and post.png).")
    parser.add_argument("--output", type=str, default="outputs/nepal_inference_results.json", help="Output JSON path for directory predictions.")
    parser.add_argument("--checkpoint", type=str, default="outputs/best_siamese_model.pth", help="Path to model checkpoint file.")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config.yaml file.")
    args = parser.parse_args()

    if not args.input_dir and not (args.pre and args.post):
        parser.error("Either --input-dir OR both --pre and --post arguments must be provided.")

    try:
        engine = DamageInference(
            checkpoint_path=args.checkpoint,
            config_path=args.config
        )

        if args.input_dir:
            summary = engine.predict_directory(args.input_dir, output_path=args.output)

            print("==================================================")
            print("         NEPAL DISASTER INFERENCE SUMMARY         ")
            print("==================================================")
            print(f"Input directory:       {args.input_dir}")
            print(f"Model checkpoint:      {args.checkpoint}")
            print(f"Device:                {summary['device']}")
            print("--------------------------------------------------")
            print(f"Total building pairs:  {summary['total_buildings']}")
            print(f"Successfully processed:{summary['processed_buildings']}")
            print(f"Failed buildings:      {summary['failed_buildings']}")
            print("--------------------------------------------------")
            print("Damage Distribution:")
            for label, count in summary["damage_distribution"].items():
                pct = summary["percentages"][label]
                print(f"  {label:<15}: {count:<5} ({pct:.2f}%)")
            print("--------------------------------------------------")
            print(f"Average Confidence:    {summary['average_confidence']:.2f}%")
            print(f"Results saved to:      {args.output}")
            print("==================================================")

        else:
            result = engine.predict_pair(args.pre, args.post)

            print("==================================================")
            print("         Disaster Damage Assessment MVP           ")
            print("==================================================")
            print(f"Pre-disaster image:  {args.pre}")
            print(f"Post-disaster image: {args.post}")
            print(f"Device:              {result['device']}")
            print("--------------------------------------------------")
            print(f"Prediction:          {result['predicted_label']}")
            print(f"Confidence:          {result['confidence'] * 100:.2f}%")
            print("--------------------------------------------------")
            print("Class Probabilities:")
            for label, prob in result["probabilities"].items():
                print(f"  {label:<15}: {prob * 100:.2f}%")
            print("==================================================")

    except Exception as e:
        print(f"[ERROR] Inference failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
