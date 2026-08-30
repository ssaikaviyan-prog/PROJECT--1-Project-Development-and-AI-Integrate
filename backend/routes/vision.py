from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

class VisionRequest(BaseModel):
    image_b64: Optional[str] = ""

router = APIRouter(prefix="/vision", tags=["Computer Vision & Multimodal Perception"])

vision_service = None

def set_vision_service(service):
    global vision_service
    vision_service = service

@router.post("/analyze")
def analyze_vision_frame(request: VisionRequest):
    if not vision_service:
        raise HTTPException(status_code=500, detail="Vision Service is not initialized.")

    try:
        perception_result = vision_service.process_image(request.image_b64 or "")
        return perception_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision analysis failed: {str(e)}")
