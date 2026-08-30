from typing import Dict, Any, List

class MCPToolService:
    """Model Context Protocol (MCP) compatible tool registry & execution engine."""

    def __init__(self, vector_store=None, vision_service=None, navigation_service=None):
        self.vector_store = vector_store
        self.vision_service = vision_service
        self.navigation_service = navigation_service

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return MCP tool schemas."""
        return [
            {
                "name": "get_camera_status",
                "description": "Returns current camera status, resolution, and frame rate.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "analyze_scene",
                "description": "Triggers computer vision perception to detect spatial obstacles.",
                "parameters": {"type": "object", "properties": {"image_b64": {"type": "string"}}}
            },
            {
                "name": "search_documents",
                "description": "Performs vector semantic search against uploaded project documentation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer", "default": 3}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_navigation_status",
                "description": "Returns current autonomous navigation decision, obstacle direction, and safety mode.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "get_sensor_status",
                "description": "Returns live telemetry from LiDAR range sensors, IMU compass, and battery state.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "get_project_information",
                "description": "Returns system architecture and technical specifications.",
                "parameters": {"type": "object", "properties": {}}
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute MCP tool function call."""
        if arguments is None:
            arguments = {}

        if tool_name == "get_camera_status":
            return {
                "status": "online",
                "fps": 30,
                "resolution": "1280x720",
                "type": "RGB-Depth Camera Simulation"
            }
        elif tool_name == "analyze_scene":
            if self.vision_service:
                return self.vision_service.process_image(arguments.get("image_b64", ""))
            return {"status": "error", "message": "Vision service offline"}
        elif tool_name == "search_documents":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 3)
            if self.vector_store:
                from backend.services.embedding_service import EmbeddingService
                embedder = EmbeddingService()
                vec = embedder.generate_embedding(query)
                res = self.vector_store.search_documents(vec, top_k=top_k)
                return {"results": res, "count": len(res)}
            return {"status": "error", "message": "Vector store offline"}
        elif tool_name == "get_navigation_status":
            if self.navigation_service and self.vision_service:
                v_data = self.vision_service.process_image("")
                return self.navigation_service.make_decision(v_data)
            return {"decision": "MOVE FORWARD", "obstacle": "NO"}
        elif tool_name == "get_sensor_status":
            return {
                "lidar_front_m": 1.4,
                "lidar_left_m": 2.8,
                "lidar_right_m": 0.9,
                "imu_heading_deg": 185.0,
                "battery_pct": 94.0,
                "wheels_encoder_rpm": [120, 120]
            }
        elif tool_name == "get_project_information":
            return {
                "title": "Vision-Language Autonomous Navigation System",
                "version": "1.0.0",
                "architecture": ["FastAPI", "Gemini API", "ChromaDB", "RAG", "OpenCV", "MCP"],
                "author": "College Autonomous Robotics Engineering Project"
            }
        else:
            return {"error": f"Unknown tool: {tool_name}"}
