import os
import json
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from backend.config import RESULTS_DIR
from backend.services.explainability_service import explainability_service

router = APIRouter(prefix="/api/explain", tags=["AI Explainability"])

class ExplainRequest(BaseModel):
    user_id: str
    assessment_id: str
    building_id: str

@router.post("")
async def explain_building_prediction(req: ExplainRequest):
    assessment_id = req.assessment_id
    building_id = req.building_id

    # 1. Locate local assessment JSON result
    result_file = os.path.join(RESULTS_DIR, f"{assessment_id}.json")
    if not os.path.exists(result_file):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment result record '{assessment_id}' not found."
        )

    try:
        with open(result_file, "r") as f:
            assessment_data = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load assessment data: {str(e)}"
        )

    # 2. Locate target building record
    buildings = assessment_data.get("BUILDINGS", [])
    target_building = None
    b_id_str = str(building_id).strip()

    for b in buildings:
        if str(b.get("building_id")).strip() == b_id_str or str(b.get("folder")).strip() == b_id_str:
            target_building = b
            break

    if not target_building:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Building '{building_id}' not found in assessment '{assessment_id}'."
        )

    # 3. Extract prediction details and image paths
    prediction = target_building.get("predicted_label", "unknown")
    confidence = float(target_building.get("confidence", 0.0))
    pre_img_path = target_building.get("pre_image", "")
    post_img_path = target_building.get("post_image", "")

    if not pre_img_path or not post_img_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building record is missing required pre or post image file references."
        )

    # 4. Generate visual explanation via Gemini
    try:
        explanation = explainability_service.generate_explanation(
            assessment_id=assessment_id,
            building_id=b_id_str,
            prediction=prediction,
            confidence=confidence,
            pre_image_path=pre_img_path,
            post_image_path=post_img_path
        )
        return explanation
    except ValueError as ve:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key is not configured on backend."
        )
    except FileNotFoundError as fnfe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image file error: {str(fnfe)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to generate AI explanation: {str(e)}"
        )
