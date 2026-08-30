import time
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, Any
from backend.services.mockapi_service import mockapi_service

router = APIRouter(prefix="/api/review", tags=["Human Review Request"])

class ReviewRequestSchema(BaseModel):
    user_id: str
    assessment_id: str
    building_id: str
    ai_prediction: str
    confidence: float
    pre_image: Optional[str] = None
    post_image: Optional[str] = None

@router.post("")
async def create_review_request(req: ReviewRequestSchema):
    review_data = {
        "USER_ID": str(req.user_id),
        "ASSESSMENT_ID": str(req.assessment_id),
        "BUILDING_ID": str(req.building_id),
        "AI_PREDICTION": str(req.ai_prediction),
        "CONFIDENCE": float(req.confidence),
        "APPROVED": False,
        "ADMIN_DECISION": "pending",
        "REVIEW_NOTE": "",
        "REVIEWED_AT": None,
        "PRE_IMAGE": req.pre_image,
        "POST_IMAGE": req.post_image,
        "REQUESTED_AT": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    return await mockapi_service.create_review_request(review_data)

@router.get("/user/{user_id}")
async def get_user_reviews(user_id: str):
    return await mockapi_service.get_reviews_by_user(user_id)
