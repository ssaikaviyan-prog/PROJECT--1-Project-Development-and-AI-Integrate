import sys
import site
import unittest
from pathlib import Path


# Enable user site-packages for dependencies
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.insert(0, user_site)

# Add project root directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


from backend.utils.config import is_gemini_key_valid, DOCUMENTS_DIR
from backend.database.vector_store import VectorStore
from backend.services.gemini_service import GeminiService
from backend.services.embedding_service import EmbeddingService
from backend.services.rag_service import RAGService
from backend.services.vision_service import VisionService
from backend.services.navigation_service import NavigationService
from backend.services.mcp_service import MCPToolService
from backend.utils.document_loader import DocumentLoader
from backend.utils.chunking import IntelligentChunker

class TestAutonomousNavigationSystem(unittest.TestCase):
    """Automated System Test Suite for Vision-Language Autonomous Navigation System."""

    @classmethod
    def setUpClass(cls):
        print("\n========================================================")
        print(" RUNNING SYSTEM VERIFICATION SUITE (TESTS 1 - 8)")
        print("========================================================")
        cls.vector_store = VectorStore()
        cls.gemini_service = GeminiService()
        cls.embedding_service = EmbeddingService()
        cls.rag_service = RAGService(cls.vector_store, cls.embedding_service, cls.gemini_service)
        cls.vision_service = VisionService(cls.gemini_service)
        cls.navigation_service = NavigationService(cls.gemini_service, cls.vision_service)
        cls.mcp_service = MCPToolService(cls.vector_store, cls.vision_service, cls.navigation_service)

    def test_01_gemini_api(self):
        """Test 1 — Gemini API Connection / Response."""
        print("[TEST 1] Testing Gemini API...")
        res = self.gemini_service.generate_text("Respond with 'OK' if you can process this message.")
        self.assertIsNotNone(res)
        self.assertTrue(len(res) > 0)
        print(f"   -> Result: {res[:60]}...")

    def test_02_embeddings(self):
        """Test 2 — Embedding Generation."""
        print("[TEST 2] Testing Gemini Embedding Generator...")
        sample_text = "Autonomous mobile robot navigation using LiDAR point clouds."
        vec = self.embedding_service.generate_embedding(sample_text)
        self.assertIsInstance(vec, list)
        self.assertTrue(len(vec) > 0)
        print(f"   -> Embedding generated with dimension {len(vec)}.")

    def test_03_vector_database(self):
        """Test 3 — Vector Database Storage & Retrieval."""
        print("[TEST 3] Testing ChromaDB Vector Store...")
        test_chunks = [{
            "chunk_id": "test_chunk_99",
            "document_id": "doc_test",
            "filename": "test_robotics.txt",
            "chunk_text": "LiDAR sensors emit laser pulses for precise obstacle distance estimation.",
            "metadata": {"filename": "test_robotics.txt", "doc_id": "doc_test"}
        }]
        embeddings = [self.embedding_service.generate_embedding(test_chunks[0]["chunk_text"])]
        
        count = self.vector_store.add_chunks(test_chunks, embeddings)
        self.assertEqual(count, 1)

        search_res = self.vector_store.search_documents(embeddings[0], top_k=1)
        self.assertTrue(len(search_res) > 0)
        self.assertEqual(search_res[0]["chunk_id"], "test_chunk_99")
        print("   -> Inserted and retrieved chunk successfully.")

    def test_04_document_loader(self):
        """Test 4 — Document Loader & Chunking Pipeline."""
        print("[TEST 4] Testing Document Extraction & Chunking...")
        sample_path = DOCUMENTS_DIR / "sample_navigation.txt"
        self.assertTrue(sample_path.exists())

        doc_info = DocumentLoader.extract_text(str(sample_path))
        self.assertIn("text", doc_info)
        self.assertTrue(len(doc_info["text"]) > 100)

        chunker = IntelligentChunker()
        chunks = chunker.create_chunks(doc_info, doc_id="doc_sample_test")
        self.assertTrue(len(chunks) > 0)
        print(f"   -> Extracted text and created {len(chunks)} chunks.")

    def test_05_rag_search(self):
        """Test 5 — RAG Vector Retrieval."""
        print("[TEST 5] Testing RAG Context Retrieval...")
        question = "What sensors can be used for obstacle detection?"
        query_vec = self.embedding_service.generate_embedding(question)
        retrieved = self.vector_store.search_documents(query_vec, top_k=3)
        self.assertTrue(len(retrieved) > 0)
        print(f"   -> Retrieved {len(retrieved)} relevant chunks for query.")

    def test_06_chatbot_rag(self):
        """Test 6 — Chatbot RAG Synthesis & Sources."""
        print("[TEST 6] Testing AI Chatbot RAG Synthesis...")
        rag_res = self.rag_service.answer_question("What is LiDAR used for?")
        self.assertIn("answer", rag_res)
        self.assertIn("sources", rag_res)
        self.assertTrue(len(rag_res["answer"]) > 0)
        print(f"   -> Chatbot Answer: {rag_res['answer'][:80]}...")
        print(f"   -> Sources: {rag_res['sources']}")

    def test_07_vision_processing(self):
        """Test 7 — Computer Vision Scene Processing."""
        print("[TEST 7] Testing Vision Perception...")
        vision_res = self.vision_service.process_image("")
        self.assertIn("obstacle_detected", vision_res)
        self.assertIn("annotated_image", vision_res)
        self.assertIn("scene_description", vision_res)
        print(f"   -> Vision Output: Obstacle={vision_res['obstacle_detected']}, Dir={vision_res['direction']}")

    def test_08_navigation_decision(self):
        """Test 8 — Autonomous Navigation Decision."""
        print("[TEST 8] Testing Navigation Decision Engine...")
        v_data = self.vision_service.process_image("")
        decision_res = self.navigation_service.make_decision(v_data)
        self.assertIn("decision", decision_res)
        self.assertIn(decision_res["decision"], ["MOVE FORWARD", "TURN LEFT", "TURN RIGHT", "STOP"])
        self.assertIn("reason", decision_res)
        print(f"   -> Navigation Decision: {decision_res['decision']} | Reason: {decision_res['reason'][:70]}...")

if __name__ == "__main__":
    unittest.main()
