import os
from typing import Optional, Dict, Any, Union, List
from PIL import Image
from inference import DamageInference
from satellite_crop_engine import SatelliteCropEngine
from backend.config import MODEL_CHECKPOINT, CONFIG_YAML

class AIService:
    def __init__(self):
        self._inference_engine: Optional[DamageInference] = None
        self._crop_engine: Optional[SatelliteCropEngine] = None

    @property
    def inference_engine(self) -> DamageInference:
        if self._inference_engine is None:
            self._inference_engine = DamageInference(
                checkpoint_path=MODEL_CHECKPOINT,
                config_path=CONFIG_YAML
            )
        return self._inference_engine

    @property
    def crop_engine(self) -> SatelliteCropEngine:
        if self._crop_engine is None:
            self._crop_engine = SatelliteCropEngine(config_path=CONFIG_YAML)
        return self._crop_engine

    def predict_building_crop_pair(self, pre_img: Union[str, Image.Image], post_img: Union[str, Image.Image]) -> Dict[str, Any]:
        return self.inference_engine.predict_pair(pre_img, post_img)

    def process_satellite_assessment(
        self,
        pre_tiff_path: str,
        post_tiff_path: str,
        geojson_path: str,
        output_crop_dir: str
    ) -> Dict[str, Any]:
        # 1. Run Satellite Crop Engine
        crop_summary = self.crop_engine.create_building_pairs(
            pre_image=pre_tiff_path,
            post_image=post_tiff_path,
            footprints=geojson_path,
            output_dir=output_crop_dir
        )

        # 2. Run Inference on extracted crops
        inference_summary = self.inference_engine.predict_directory(
            input_dir=output_crop_dir,
            output_path=os.path.join(output_crop_dir, "results.json")
        )

        return {
            "crop_summary": crop_summary,
            "inference_summary": inference_summary
        }

ai_service = AIService()
