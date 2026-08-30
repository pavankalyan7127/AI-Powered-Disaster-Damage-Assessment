import os
import json
from fastapi import APIRouter, HTTPException
from backend.services.mockapi_service import mockapi_service
from backend.config import RESULTS_DIR

router = APIRouter(prefix="/api/history", tags=["History"])

@router.get("/{user_id}")
async def get_user_history(user_id: str):
    """
    Returns lightweight assessment metadata list for the specified user from MockAPI.
    """
    try:
        return await mockapi_service.get_history_by_user(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history metadata: {str(e)}")

@router.get("/{user_id}/{assessment_id}")
async def get_assessment_detail(user_id: str, assessment_id: str):
    """
    Retrieves HISTORY metadata and merges complete inference results from the local JSON file.
    """
    # 1. Check local JSON file directly
    local_file = os.path.join(RESULTS_DIR, f"{assessment_id}.json")
    if os.path.exists(local_file):
        try:
            with open(local_file, "r") as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read local assessment result file: {str(e)}")

    # 2. Fallback: Lookup in MockAPI
    history_record = await mockapi_service.get_history_by_assessment_id(user_id, assessment_id)
    if not history_record:
        raise HTTPException(status_code=404, detail="Assessment history record not found.")

    # Check if history record references a result file
    result_file = history_record.get("RESULT_FILE")
    if result_file:
        file_path = os.path.join(RESULTS_DIR, result_file)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)

    # If BUILDINGS array is present directly in history record (legacy records)
    if "BUILDINGS" in history_record and history_record["BUILDINGS"]:
        return history_record

    raise HTTPException(
        status_code=404,
        detail=f"Local result file for assessment '{assessment_id}' could not be located."
    )
