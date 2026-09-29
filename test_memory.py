import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.agents import AgentRuntime
from app.demo import run_learning_demo
from app.auth import create_token, verify_token
from app.memory_service import MemoryService

class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.svc = MemoryService(os.path.join(tempfile.mkdtemp(), "t.db"))
        self.rt = AgentRuntime(self.svc)

    def test_retain_and_recall(self):
        self.svc.retain("sales", "outcome", "Deal with Fabrikam won at $50000 vs HubSpot", ["deal"], ["Fabrikam"])
        r = self.svc.recall("Fabrikam deal", agent="sales")
        self.assertTrue(r and "Fabrikam" in r[0]["text"])

    def test_reinforcement_moves_confidence(self):
        m = self.svc.retain("support", "success", "restart fixes cache", confidence=0.5)
        up = self.svc.reinforce(m["id"], True)["confidence"]
        down = self.svc.reinforce(m["id"], False)["confidence"]
        self.assertGreater(up, 0.5); self.assertLess(down, up)

    def test_decay_drops_with_age(self):
        m = self.svc.retain("support", "episodic", "old note")
        self.assertLess(self.svc.store.decay(m, now=m["last_used"] + 120 * 86400), 0.3)

    def test_learning_loop_improves_answer(self):
        out = run_learning_demo(self.rt)
        self.assertTrue(out["improved"])
        self.assertIn("certificate", out["after_learning"]["answer"].lower())
        self.assertIn("Avoid", out["after_learning"]["answer"])
        self.assertTrue(out["other_agent_benefits"]["memory_used"])  # shared brain

    def test_graph_and_stats(self):
        run_learning_demo(self.rt)
        g = self.svc.store.graph()
        self.assertTrue(any(n["id"] == "Contoso" for n in g["nodes"]))
        self.assertGreater(self.svc.status()["local"]["total"], 3)

    def test_jwt(self):
        self.assertEqual(verify_token(create_token("a"))["sub"], "a")
        self.assertIsNone(verify_token(create_token("a") + "x"))

if __name__ == "__main__":
    unittest.main()
