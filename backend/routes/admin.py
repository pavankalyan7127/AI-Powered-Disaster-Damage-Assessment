import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
from backend.services.mockapi_service import mockapi_service

router = APIRouter(prefix="/api/admin", tags=["Admin Management"])

class AdminDecisionSchema(BaseModel):
    approved: bool
    admin_decision: str # "approved" or "overridden"
    review_note: str

@router.get("/reviews")
async def get_admin_reviews():
    return await mockapi_service.get_pending_reviews()

@router.put("/reviews/{review_id}")
async def update_review_decision(review_id: str, req: AdminDecisionSchema):
    update_payload = {
        "APPROVED": req.approved,
        "ADMIN_DECISION": req.admin_decision,
        "REVIEW_NOTE": req.review_note,
        "REVIEWED_AT": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        updated_review = await mockapi_service.update_review(review_id, update_payload)
        return updated_review
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update review record: {str(e)}")
