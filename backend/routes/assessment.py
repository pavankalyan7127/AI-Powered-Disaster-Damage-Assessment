import os
import uuid
import json
import time
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from PIL import Image

from backend.config import (
    UPLOADS_DIR, OUTPUTS_DIR, RESULTS_DIR,
    NEPAL_PRE_TIFF, NEPAL_POST_TIFF, NEPAL_FOOTPRINTS_GEOJSON, NEPAL_PRECOMPUTED_JSON
)
from backend.services.ai_service import ai_service
from backend.services.mockapi_service import mockapi_service

router = APIRouter(prefix="/api/assessment", tags=["Assessment"])

def _save_local_result(assessment_id: str, complete_result: dict) -> str:
    """
    Saves the complete inference result JSON locally under outputs/inference_results/<assessment_id>.json.
    Returns the relative result file path.
    """
    file_name = f"{assessment_id}.json"
    local_path = os.path.join(RESULTS_DIR, file_name)
    with open(local_path, "w") as f:
        json.dump(complete_result, f, indent=2)
    return file_name

@router.post("/satellite")
async def run_satellite_assessment(
    user_id: str = Form(...),
    is_nepal_demo: bool = Form(False),
    pre_file: Optional[UploadFile] = File(None),
    post_file: Optional[UploadFile] = File(None),
    geojson_file: Optional[UploadFile] = File(None)
):
    assessment_id = f"assessment_{uuid.uuid4().hex[:8]}"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # 1. Handle Nepal Quick Ready Demo vs Custom Satellite Assessment
    if is_nepal_demo:
        if os.path.exists(NEPAL_PRECOMPUTED_JSON):
            with open(NEPAL_PRECOMPUTED_JSON, "r") as f:
                precomputed_data = json.load(f)

            complete_record = {
                "USER_ID": str(user_id),
                "ASSESSMENT_ID": assessment_id,
                "TIMESTAMP": timestamp,
                "INPUT_MODE": "satellite_nepal_demo",
                "TOTAL_BUILDINGS": precomputed_data.get("total_buildings", 0),
                "DAMAGE_DISTRIBUTION": precomputed_data.get("damage_distribution", {}),
                "PERCENTAGES": precomputed_data.get("percentages", {}),
                "AVERAGE_CONFIDENCE": precomputed_data.get("average_confidence", 0.0),
                "BUILDINGS": precomputed_data.get("buildings", [])
            }
        else:
            pre_path = NEPAL_PRE_TIFF
            post_path = NEPAL_POST_TIFF
            geojson_path = NEPAL_FOOTPRINTS_GEOJSON

            output_crop_dir = os.path.join(OUTPUTS_DIR, "inference_crops", assessment_id)
            try:
                results = ai_service.process_satellite_assessment(
                    pre_tiff_path=pre_path,
                    post_tiff_path=post_path,
                    geojson_path=geojson_path,
                    output_crop_dir=output_crop_dir
                )
                inf_summary = results["inference_summary"]
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Nepal satellite assessment processing failed: {str(e)}")

            complete_record = {
                "USER_ID": str(user_id),
                "ASSESSMENT_ID": assessment_id,
                "TIMESTAMP": timestamp,
                "INPUT_MODE": "satellite_nepal_demo",
                "TOTAL_BUILDINGS": inf_summary.get("total_buildings", 0),
                "DAMAGE_DISTRIBUTION": inf_summary.get("damage_distribution", {}),
                "PERCENTAGES": inf_summary.get("percentages", {}),
                "AVERAGE_CONFIDENCE": inf_summary.get("average_confidence", 0.0),
                "BUILDINGS": inf_summary.get("buildings", [])
            }
    else:
        if not pre_file or not post_file or not geojson_file:
            raise HTTPException(status_code=400, detail="Missing required input files for satellite assessment.")
        
        session_dir = os.path.join(UPLOADS_DIR, assessment_id)
        os.makedirs(session_dir, exist_ok=True)

        pre_path = os.path.join(session_dir, "pre.tif")
        post_path = os.path.join(session_dir, "post.tif")
        geojson_path = os.path.join(session_dir, "footprints.geojson")

        with open(pre_path, "wb") as f:
            f.write(await pre_file.read())
        with open(post_path, "wb") as f:
            f.write(await post_file.read())
        with open(geojson_path, "wb") as f:
            f.write(await geojson_file.read())

        output_crop_dir = os.path.join(OUTPUTS_DIR, "inference_crops", assessment_id)
        try:
            results = ai_service.process_satellite_assessment(
                pre_tiff_path=pre_path,
                post_tiff_path=post_path,
                geojson_path=geojson_path,
                output_crop_dir=output_crop_dir
            )
            inf_summary = results["inference_summary"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Satellite assessment processing failed: {str(e)}")

        complete_record = {
            "USER_ID": str(user_id),
            "ASSESSMENT_ID": assessment_id,
            "TIMESTAMP": timestamp,
            "INPUT_MODE": "satellite",
            "TOTAL_BUILDINGS": inf_summary.get("total_buildings", 0),
            "DAMAGE_DISTRIBUTION": inf_summary.get("damage_distribution", {}),
            "PERCENTAGES": inf_summary.get("percentages", {}),
            "AVERAGE_CONFIDENCE": inf_summary.get("average_confidence", 0.0),
            "BUILDINGS": inf_summary.get("buildings", [])
        }

    # 2. Save complete inference result JSON locally
    result_filename = _save_local_result(assessment_id, complete_record)

    # 3. Create lightweight metadata record for MockAPI (EXCLUDES huge BUILDINGS array)
    lightweight_history_record = {
        "USER_ID": str(user_id),
        "ASSESSMENT_ID": assessment_id,
        "TIMESTAMP": timestamp,
        "INPUT_MODE": complete_record["INPUT_MODE"],
        "TOTAL_BUILDINGS": complete_record["TOTAL_BUILDINGS"],
        "DAMAGE_DISTRIBUTION": complete_record["DAMAGE_DISTRIBUTION"],
        "PERCENTAGES": complete_record.get("PERCENTAGES", {}),
        "AVERAGE_CONFIDENCE": complete_record["AVERAGE_CONFIDENCE"],
        "RESULT_FILE": result_filename
    }

    try:
        await mockapi_service.create_history(lightweight_history_record)
    except Exception as e:
        print(f"[WARNING] MockAPI create history failed: {e}. Local result preserved.")

    # Return complete record to caller for immediate Results Page rendering
    return complete_record


@router.post("/building")
async def run_building_crop_assessment(
    user_id: str = Form(...),
    pre_image: UploadFile = File(...),
    post_image: UploadFile = File(...)
):
    assessment_id = f"assessment_{uuid.uuid4().hex[:8]}"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    session_dir = os.path.join(UPLOADS_DIR, assessment_id)
    os.makedirs(session_dir, exist_ok=True)

    pre_path = os.path.join(session_dir, "pre.png")
    post_path = os.path.join(session_dir, "post.png")

    try:
        pil_pre = Image.open(pre_image.file).convert("RGB")
        pil_post = Image.open(post_image.file).convert("RGB")

        pil_pre.save(pre_path)
        pil_post.save(post_path)

        pred_res = ai_service.predict_building_crop_pair(pil_pre, pil_post)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid building crop image input: {str(e)}")

    building_entry = {
        "building_id": "b_direct_01",
        "folder": assessment_id,
        "pre_image": pre_path,
        "post_image": post_path,
        "predicted_class": pred_res["predicted_class"],
        "predicted_label": pred_res["predicted_label"],
        "confidence": pred_res["confidence"],
        "probabilities": pred_res["probabilities"]
    }

    damage_distribution = {
        "no-damage": 1 if pred_res["predicted_label"] == "no-damage" else 0,
        "minor-damage": 1 if pred_res["predicted_label"] == "minor-damage" else 0,
        "major-damage": 1 if pred_res["predicted_label"] == "major-damage" else 0,
        "destroyed": 1 if pred_res["predicted_label"] == "destroyed" else 0
    }

    complete_record = {
        "USER_ID": str(user_id),
        "ASSESSMENT_ID": assessment_id,
        "TIMESTAMP": timestamp,
        "INPUT_MODE": "building_crop",
        "TOTAL_BUILDINGS": 1,
        "DAMAGE_DISTRIBUTION": damage_distribution,
        "PERCENTAGES": {k: (100.0 if v == 1 else 0.0) for k, v in damage_distribution.items()},
        "AVERAGE_CONFIDENCE": round(pred_res["confidence"] * 100, 2),
        "BUILDINGS": [building_entry]
    }

    # Save local JSON
    result_filename = _save_local_result(assessment_id, complete_record)

    # Lightweight MockAPI history entry
    lightweight_history_record = {
        "USER_ID": str(user_id),
        "ASSESSMENT_ID": assessment_id,
        "TIMESTAMP": timestamp,
        "INPUT_MODE": "building_crop",
        "TOTAL_BUILDINGS": 1,
        "DAMAGE_DISTRIBUTION": damage_distribution,
        "PERCENTAGES": complete_record["PERCENTAGES"],
        "AVERAGE_CONFIDENCE": complete_record["AVERAGE_CONFIDENCE"],
        "RESULT_FILE": result_filename
    }

    try:
        await mockapi_service.create_history(lightweight_history_record)
    except Exception as e:
        print(f"[WARNING] MockAPI create history failed: {e}. Local result preserved.")

    return complete_record
