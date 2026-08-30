from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

class NavigationRequest(BaseModel):
    image_b64: Optional[str] = ""
    sensor_telemetry: Optional[Dict[str, Any]] = None

router = APIRouter(prefix="/navigation", tags=["Autonomous Navigation Decision System"])

navigation_service = None
vision_service = None
active_telemetry = None

def set_navigation_services(nav_service, vis_service):
    global navigation_service, vision_service
    navigation_service = nav_service
    vision_service = vis_service

@router.get("/status")
def get_navigation_status():
    if not navigation_service or not vision_service:
        raise HTTPException(status_code=500, detail="Navigation service is not initialized.")

    v_data = vision_service.process_image("")
    decision_res = navigation_service.make_decision(v_data, active_telemetry)
    return decision_res

@router.post("/decision")
def compute_navigation_decision(request: NavigationRequest):
    if not navigation_service or not vision_service:
        raise HTTPException(status_code=500, detail="Navigation service is not initialized.")

    global active_telemetry
    if request.sensor_telemetry is not None:
        active_telemetry = request.sensor_telemetry

    v_data = vision_service.process_image(request.image_b64 or "")
    decision_res = navigation_service.make_decision(v_data, active_telemetry)
    return decision_res
