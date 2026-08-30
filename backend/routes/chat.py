import os
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from PIL import Image
from google import genai
from google.genai import types

from backend.config import GEMINI_API_KEY, RESULTS_DIR, EXPLANATION_CACHE_DIR

router = APIRouter(prefix="/api/building-chat", tags=["Building Chat AI"])

class ChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    user_id: str
    assessment_id: str
    building_id: str
    message: str
    history: Optional[List[ChatMessage]] = []

def _get_genai_client() -> genai.Client:
    key = os.getenv("GEMINI_API_KEY", "") or GEMINI_API_KEY
    if not key or key.strip() == "":
        raise ValueError("GEMINI_API_KEY is not configured on backend.")
    return genai.Client(api_key=key.strip())

@router.post("")
async def chat_about_building(req: ChatRequest):
    # 1. Validate assessment result file
    result_file = os.path.join(RESULTS_DIR, f"{req.assessment_id}.json")
    if not os.path.exists(result_file):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment record '{req.assessment_id}' not found."
        )

    try:
        with open(result_file, "r") as f:
            assessment_data = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read assessment data: {str(e)}"
        )

    # 2. Locate building in assessment
    buildings = assessment_data.get("BUILDINGS", [])
    target_building = None
    b_id_str = str(req.building_id).strip()

    for b in buildings:
        if str(b.get("building_id")).strip() == b_id_str or str(b.get("folder")).strip() == b_id_str:
            target_building = b
            break

    if not target_building:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Building '{req.building_id}' not found in assessment '{req.assessment_id}'."
        )

    # 3. Check for cached visual explanation if available
    cache_key = f"{req.assessment_id}_{b_id_str}.json".replace("/", "_").replace("\\", "_")
    cache_path = os.path.join(EXPLANATION_CACHE_DIR, cache_key)
    existing_explanation = ""
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                exp_json = json.load(f)
                existing_explanation = exp_json.get("explanation", "")
        except Exception:
            pass

    # 4. Extract building details
    prediction = target_building.get("predicted_label", "unknown")
    confidence = float(target_building.get("confidence", 0.0))
    pre_img_path = target_building.get("pre_image", "")
    post_img_path = target_building.get("post_image", "")
    probabilities = target_building.get("probabilities", {})

    # System instruction / System prompt
    system_instruction = f"""
You are an expert Disaster Assessment AI Assistant embedded in a mission-critical disaster response portal.
You are currently providing analysis specifically for Building ID: {b_id_str} under Assessment ID: {req.assessment_id}.

SPECIFIC BUILDING CONTEXT:
- Building ID: {b_id_str}
- Assessment ID: {req.assessment_id}
- Computer Vision (CV) Model Prediction: {prediction}
- Model Confidence: {confidence * 100:.1f}%
- Class Probabilities: {json.dumps(probabilities)}
- Pre-Disaster Image Path: {pre_img_path}
- Post-Disaster Image Path: {post_img_path}
- Cached AI Visual Explanation: {existing_explanation or "None generated yet"}

IMPORTANT SAFETY & COMPLIANCE RULES:
1. When asked about structural safety, re-entry, or entering/approaching the building (e.g. "Is it safe to enter/be near this building?"):
   - NEVER give an absolute guarantee such as "Yes, it is safe."
   - Explicitly state that you are a computer vision damage assessment tool and CANNOT certify structural safety.
   - Explain that a building classified as '{prediction}' should be treated as potentially hazardous and must be evaluated on-site by certified structural engineers or emergency personnel prior to entry.
2. Clearly distinguish between:
   - The authoritative Computer Vision model prediction ({prediction})
   - Observable visual changes in the satellite/building crop imagery
   - Certified physical structural safety
3. Be concise, objective, professional, and clear. Do not invent non-existent damage.
"""

    # Build prompt contents with images if available
    contents = [system_instruction]

    if os.path.exists(pre_img_path) and os.path.exists(post_img_path):
        try:
            pre_img = Image.open(pre_img_path).convert("RGB")
            post_img = Image.open(post_img_path).convert("RGB")
            contents.extend([
                "PRE-DISASTER BUILDING CROP IMAGE:", pre_img,
                "POST-DISASTER BUILDING CROP IMAGE:", post_img
            ])
        except Exception as img_err:
            print(f"[WARNING] Could not open images for building chat: {img_err}")

    # Append chat history
    if req.history:
        history_text = "\nPREVIOUS CONVERSATION HISTORY:\n"
        for msg in req.history[-6:]: # Limit to last 6 messages
            history_text += f"{msg.role.upper()}: {msg.content}\n"
        contents.append(history_text)

    contents.append(f"USER QUESTION: {req.message}")

    # 5. Call Gemini API
    try:
        client = _get_genai_client()
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.3
            )
        )

        if not response or not response.text:
            raise RuntimeError("Gemini API returned an empty response.")

        return {
            "building_id": b_id_str,
            "assessment_id": req.assessment_id,
            "reply": response.text.strip()
        }

    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API key is not configured on backend."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process AI chat message. Please try again."
        )
