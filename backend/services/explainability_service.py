import os
import json
from typing import Dict, Any, Optional
from PIL import Image
from google import genai
from google.genai import types

from backend.config import GEMINI_API_KEY, EXPLANATION_CACHE_DIR

class ExplainabilityService:
    def _get_client(self) -> genai.Client:
        key = os.getenv("GEMINI_API_KEY", "") or GEMINI_API_KEY
        if not key or key.strip() == "":
            raise ValueError("GEMINI_API_KEY is missing or empty in environment/backend configuration.")
        return genai.Client(api_key=key.strip())

    def generate_explanation(
        self,
        assessment_id: str,
        building_id: str,
        prediction: str,
        confidence: float,
        pre_image_path: str,
        post_image_path: str
    ) -> Dict[str, Any]:
        # 1. Check local cache first (assessment_id + building_id)
        cache_key = f"{assessment_id}_{building_id}.json".replace("/", "_").replace("\\", "_")
        cache_path = os.path.join(EXPLANATION_CACHE_DIR, cache_key)

        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass # Re-generate on cache read error

        # 2. Validate Image existence
        if not os.path.exists(pre_image_path):
            raise FileNotFoundError(f"PRE image path not found: {pre_image_path}")
        if not os.path.exists(post_image_path):
            raise FileNotFoundError(f"POST image path not found: {post_image_path}")

        # Open PIL images
        pre_img = Image.open(pre_image_path).convert("RGB")
        post_img = Image.open(post_image_path).convert("RGB")

        prompt = f"""
You are assisting a disaster damage assessment system.

Compare the provided PRE-DISASTER and POST-DISASTER images of the same building crop.

The existing computer vision AI model predicted:
Prediction: {prediction}
Confidence: {confidence * 100:.1f}%

Explain the visible visual changes between the pre-disaster and post-disaster images that are relevant to this prediction.

Important guidelines:
- Do not invent damage that cannot be visually observed.
- Clearly distinguish visible evidence from uncertainty.
- Do not change or override the existing model prediction.
- Do not claim that your explanation proves the prediction is correct.
- Focus on observable structural or environmental changes (e.g. roof collapse, debris, structural deformation, color changes, vegetation loss).
- If the images are unclear, low resolution, or insufficient to determine the exact cause, explicitly state that in limitations.
- Keep the explanation concise and suitable for a disaster assessment dashboard.

Output JSON matching this exact schema:
{{
  "prediction": "{prediction}",
  "confidence": {confidence},
  "visual_changes": [
    "Short bullet point 1 describing visual change",
    "Short bullet point 2 describing visual change"
  ],
  "explanation": "Clear, 2-3 sentence visual summary explaining why the pre vs post changes correspond to the prediction.",
  "evidence_level": "high | medium | low",
  "limitations": "Any imagery constraints, resolution limits, or shadow/lighting ambiguity."
}}
"""

        client = self._get_client()

        # Primary model gemini-3.6-flash with fallbacks
        candidate_models = ['gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-3-flash-preview']
        response = None
        last_err = None

        for m_name in candidate_models:
            try:
                response = client.models.generate_content(
                    model=m_name,
                    contents=[
                        "PRE-DISASTER IMAGE:", pre_img,
                        "POST-DISASTER IMAGE:", post_img,
                        prompt
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2,
                        tools=[] # Explicitly disable tool / function calling to prevent AFC warnings/delays
                    )
                )
                if response and response.text:
                    break
            except Exception as ex:
                last_err = ex
                continue

        if not response or not response.text:
            raise RuntimeError(f"Gemini API generation failed: {last_err}")

        # Parse output JSON
        raw_text = response.text
        try:
            explanation_data = json.loads(raw_text)
        except json.JSONDecodeError:
            explanation_data = {
                "prediction": prediction,
                "confidence": confidence,
                "visual_changes": ["Visual comparison processed."],
                "explanation": raw_text.strip(),
                "evidence_level": "medium",
                "limitations": "Unstructured response parsed."
            }

        # Enforce exact authoritative prediction and confidence from model
        explanation_data["prediction"] = prediction
        explanation_data["confidence"] = confidence

        # Save to local cache
        try:
            with open(cache_path, "w") as f:
                json.dump(explanation_data, f, indent=2)
        except Exception:
            pass

        return explanation_data

explainability_service = ExplainabilityService()
