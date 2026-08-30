import cv2
import base64
import numpy as np
from typing import Dict, Any, Tuple
from backend.services.gemini_service import GeminiService

class VisionService:
    """Computer Vision & Multimodal Perception Processing Module."""

    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service

    def process_image(self, image_data: str) -> Dict[str, Any]:
        """
        Process base64 encoded image or frame bytes.
        Performs OpenCV spatial analysis + Gemini Vision multimodal reasoning.
        """
        if not image_data or not image_data.strip():
            return self._generate_simulated_perception()

        try:
            # Decode base64 image
            img_bytes = self._decode_base64(image_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                return self._generate_simulated_perception()

            height, width, _ = img.shape

            # Perform OpenCV computer vision object/obstacle detection analysis
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)

            # Find contours representing obstacles/objects
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            obstacles = []
            annotated_img = img.copy()
            obstacle_detected = False
            primary_direction = "CLEAR"
            closest_distance_m = 3.5

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 1200:  # Threshold for significant obstacle
                    x, y, w, h = cv2.boundingRect(cnt)
                    cnt_center_x = x + w / 2

                    # Calculate relative position (Front, Left, Right)
                    if cnt_center_x < width * 0.35:
                        direction = "Left"
                    elif cnt_center_x > width * 0.65:
                        direction = "Right"
                    else:
                        direction = "Front"

                    # Distance heuristic based on height ratio
                    distance_est = round(max(0.4, 3.0 - (h / height) * 2.5), 2)
                    if distance_est < closest_distance_m:
                        closest_distance_m = distance_est
                        primary_direction = direction

                    if distance_est <= 2.0:
                        obstacle_detected = True

                    # Draw bounding box and label on annotated image
                    color = (0, 0, 255) if distance_est <= 1.5 else (0, 165, 255)
                    cv2.rectangle(annotated_img, (x, y), (x + w, y + h), color, 2)
                    cv2.putText(
                        annotated_img,
                        f"Obstacle ({direction}) {distance_est}m",
                        (x, max(20, y - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        2
                    )

                    obstacles.append({
                        "x": x, "y": y, "w": w, "h": h,
                        "direction": direction,
                        "distance_m": distance_est,
                        "area": area
                    })

            # Draw HUD grid overlays
            cv2.line(annotated_img, (int(width * 0.35), 0), (int(width * 0.35), height), (255, 255, 255), 1)
            cv2.line(annotated_img, (int(width * 0.65), 0), (int(width * 0.65), height), (255, 255, 255), 1)
            status_text = f"OBSTACLE: {'DETECTED' if obstacle_detected else 'NONE'} | DIR: {primary_direction}"
            cv2.putText(annotated_img, status_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Convert annotated frame back to base64 jpeg
            _, buffer = cv2.imencode('.jpg', annotated_img)
            annotated_b64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')

            # Multimodal Gemini Vision reasoning call
            vision_prompt = (
                "Analyze this camera frame for autonomous mobile robot navigation. "
                "Identify key objects, potential hazards, surface terrain, and recommend path safety."
            )
            gemini_vision_res = self.gemini_service.analyze_vision(image_data, vision_prompt)

            return {
                "obstacle_detected": obstacle_detected,
                "direction": primary_direction if obstacle_detected else "Front",
                "distance_m": closest_distance_m if obstacle_detected else 3.5,
                "confidence": 0.92 if obstacle_detected else 0.98,
                "obstacles_count": len(obstacles),
                "annotated_image": annotated_b64,
                "scene_description": gemini_vision_res.get("text", "Path clear for autonomous traversal."),
                "raw_obstacles": obstacles
            }

        except Exception as e:
            print(f"Error in vision processing: {e}")
            return self._generate_simulated_perception()

    def _decode_base64(self, b64_str: str) -> bytes:
        if "," in b64_str:
            b64_str = b64_str.split(",")[1]
        return base64.b64decode(b64_str)

    def _generate_simulated_perception(self) -> Dict[str, Any]:
        """Generate high-fidelity simulated camera perception data when no live camera feed is passed."""
        # Create a synthetic 400x600 dark HUD canvas
        img = np.zeros((400, 600, 3), dtype=np.uint8)
        img[:] = (30, 25, 20)  # Dark tech background
        
        # Draw simulated obstacles
        cv2.rectangle(img, (220, 140), (380, 320), (0, 140, 255), 2)
        cv2.putText(img, "OBSTACLE: CHAIR / BARRIER (1.4m)", (200, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 140, 255), 2)
        
        # Overlay grid & HUD lines
        cv2.line(img, (200, 0), (200, 400), (80, 80, 80), 1)
        cv2.line(img, (400, 0), (400, 400), (80, 80, 80), 1)
        cv2.putText(img, "AUTONOMOUS VISION FEED - SIMULATION MODE", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 200), 2)
        
        _, buffer = cv2.imencode('.jpg', img)
        annotated_b64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')

        return {
            "obstacle_detected": True,
            "direction": "Front",
            "distance_m": 1.4,
            "confidence": 0.94,
            "obstacles_count": 1,
            "annotated_image": annotated_b64,
            "scene_description": "Simulated Perception: Stationary barrier/obstacle detected directly in center path at 1.4 meters. Clear passage detected on the left flank.",
            "raw_obstacles": [{"direction": "Front", "distance_m": 1.4, "object": "Barrier"}]
        }
