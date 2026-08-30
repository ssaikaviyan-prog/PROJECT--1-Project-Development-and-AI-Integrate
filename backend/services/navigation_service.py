from typing import Dict, Any
from backend.services.gemini_service import GeminiService
from backend.services.vision_service import VisionService

class NavigationService:
    """Autonomous Navigation Logic & Safety Decision Engine."""

    def __init__(self, gemini_service: GeminiService, vision_service: VisionService):
        self.gemini_service = gemini_service
        self.vision_service = vision_service

    def make_decision(self, vision_data: Dict[str, Any], sensor_telemetry: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process vision metrics & sensor telemetry to generate autonomous navigation decisions.
        """
        if not sensor_telemetry:
            sensor_telemetry = {
                "lidar_front_m": vision_data.get("distance_m", 1.4) if vision_data.get("obstacle_detected") else 3.5,
                "lidar_left_m": 2.8,
                "lidar_right_m": 0.9,
                "battery_pct": 94.0,
                "heading_deg": 185.0
            }

        # If sensor_telemetry is provided, override obstacle detection logic
        if sensor_telemetry:
            lidar_front = sensor_telemetry.get("lidar_front_m", 3.5)
            lidar_left = sensor_telemetry.get("lidar_left_m", 2.5)
            lidar_right = sensor_telemetry.get("lidar_right_m", 2.5)
            
            front_warning = lidar_front <= 2.0
            left_warning = lidar_left <= 1.5
            right_warning = lidar_right <= 1.5
            
            obstacle_detected = front_warning or left_warning or right_warning
            confidence = 0.94
            
            if obstacle_detected:
                # Set direction based on closest obstacle
                if front_warning and (lidar_front <= lidar_left and lidar_front <= lidar_right):
                    direction = "Front"
                    distance_m = lidar_front
                elif left_warning and (lidar_left <= lidar_front and lidar_left <= lidar_right):
                    direction = "Left"
                    distance_m = lidar_left
                else:
                    direction = "Right"
                    distance_m = lidar_right
            else:
                direction = "Front"
                distance_m = lidar_front
        else:
            obstacle_detected = vision_data.get("obstacle_detected", False)
            direction = vision_data.get("direction", "Front")
            distance_m = vision_data.get("distance_m", 3.5)
            confidence = vision_data.get("confidence", 0.92)
            lidar_front = distance_m
            lidar_left = 2.5
            lidar_right = 2.5

        # Rule-Based Safety State Machine
        if obstacle_detected and lidar_front <= 0.8:
            decision = "STOP"
            reason_default = f"Emergency stop triggered: Critical obstacle within {lidar_front}m directly in front."
        elif obstacle_detected and direction == "Front":
            if lidar_left > lidar_right:
                decision = "TURN LEFT"
                reason_default = f"Front path obstructed at {lidar_front}m. Left flank is clear ({lidar_left}m open space)."
            else:
                decision = "TURN RIGHT"
                reason_default = f"Front path obstructed at {lidar_front}m. Right flank is clear ({lidar_right}m open space)."
        elif obstacle_detected and direction == "Left":
            decision = "TURN RIGHT"
            reason_default = f"Obstacle detected on Left flank ({distance_m}m). Adjusting trajectory to the right."
        elif obstacle_detected and direction == "Right":
            decision = "TURN LEFT"
            reason_default = f"Obstacle detected on Right flank ({distance_m}m). Adjusting trajectory to the left."
        else:
            decision = "MOVE FORWARD"
            reason_default = "Front pathway clear. No significant collisions predicted within 3.0 meters."

        # Enhance decision reasoning with Gemini LLM synthesis
        prompt = (
            f"Autonomous Navigation Control System:\n"
            f"- Obstacle Detected: {'YES' if obstacle_detected else 'NO'}\n"
            f"- Obstacle Position: {direction}\n"
            f"- Distance Estimate: {distance_m}m\n"
            f"- LiDAR Front: {lidar_front}m, Left: {lidar_left}m, Right: {lidar_right}m\n"
            f"- Computed Action: {decision}\n\n"
            f"Provide a concise, 1-2 sentence engineering explanation for selecting '{decision}'."
        )

        reasoning = self.gemini_service.generate_text(prompt)
        if "Fallback" in reasoning or len(reasoning) < 10:
            reasoning = reason_default

        return {
            "status": "active",
            "mode": "autonomous",
            "detected": {
                "obstacle": "YES" if obstacle_detected else "NO",
                "direction": direction,
                "distance_m": distance_m,
                "confidence_pct": int(confidence * 100)
            },
            "telemetry": {
                "lidar_front_m": lidar_front,
                "lidar_left_m": lidar_left,
                "lidar_right_m": lidar_right,
                "battery_pct": sensor_telemetry.get("battery_pct", 95.0),
                "heading_deg": sensor_telemetry.get("heading_deg", 180.0)
            },
            "decision": decision,
            "reason": reasoning
        }
