import unittest
from unittest.mock import patch
from plenum_ai import agentpeerchat_council as c

OWNER, QWEN, GEMINI, THREAD = "hum_owner", "agt_qwen", "agt_gemini", "thr_1234567890"


class FakeAPI:
    def __init__(self, incoming, own=QWEN, replied=False):
        self.incoming, self.own, self.replied = incoming, own, replied
        self.sent, self.acked = [], []
        self.principals = [
            {"id": OWNER, "kind": "owner", "active": 1, "name": "Founder"},
            {"id": QWEN, "kind": "agent", "active": 1, "name": c.AGENTS["qwen"]},
            {"id": GEMINI, "kind": "agent", "active": 1, "name": c.AGENTS["gemini"]},
        ]

    def ack(self, message_id):
        return self.request("/messages/" + message_id + "/ack", method="POST")

    def request(self, path, payload=None, idempotency=None, method=None):
        if path == "/me":
            return {"principal": {"id": self.own}}
        if path.startswith("/inbox?"):
            return {"items": self.incoming}
        if path == "/principals":
            return {"items": self.principals}
        if path.startswith("/threads/"):
            return {"thread": {"title": c.TITLE, "members": self.principals},
                    "items": ([{"sender_id": self.own, "reply_to": self.incoming[0]["id"]}]
                              if self.replied else []), "has_more": False}
        if path == "/messages":
            self.sent.append((payload, idempotency))
            return {"message": {"id": "msg_reply"}}
        if path.endswith("/ack"):
            self.acked.append(path)
            return {"acked_at": "now"}
        raise ValueError(path)


class CouncilBridgeTests(unittest.TestCase):
    def test_only_approved_instance(self):
        with self.assertRaises(ValueError):
            c.config("qwen", {"PLENUM_APC_QWEN_KEY": "x" * 32,
                               "PLENUM_APC_URL": "https://other.example"})
        with self.assertRaises(ValueError):
            c.config("qwen", {"PLENUM_APC_QWEN_KEY": "x" * 32,
                               "PLENUM_APC_URL": "https://agentpeerchat.chadkhalil21.workers.dev:444"})

    def test_missing_key_no_run(self):
        self.assertEqual(c.run("qwen", {}), {
            "status": "BLOCKED_MISSING_AGENT_KEY", "processed": 0})

    def test_initial_owner_question(self):
        m = {"id": "msg_123", "thread_id": THREAD,
             "sender_id": OWNER, "type": "text", "content": "Any public marketing ideas?"}
        self.assertEqual(c.classify(m, "qwen", {OWNER: {"kind": "owner"}}, QWEN)[0], "initial")

    def test_peer_critique_has_one_round(self):
        peer = {GEMINI: {"kind": "agent", "name": c.AGENTS["gemini"]}}
        m = {"id": "msg_123", "thread_id": THREAD, "sender_id": GEMINI,
             "type": "text", "content": c.MARKERS["gemini"] + "\nIdea"}
        self.assertEqual(c.classify(m, "qwen", peer, QWEN), ("critique", "Idea"))
        m["content"] = c.CRITIQUE["gemini"] + "\nCritique"
        self.assertIsNone(c.classify(m, "qwen", peer, QWEN))

    def test_owner_member_required(self):
        api = FakeAPI([])
        self.assertIn(OWNER, c.members_for(api, THREAD))
        api.principals = api.principals[1:]
        self.assertIsNone(c.members_for(api, THREAD))

    def test_send_then_ack(self):
        m = {"id": "msg_123", "thread_id": THREAD,
             "sender_id": OWNER, "type": "text", "content": "What is an idea?"}
        api = FakeAPI([m])
        with patch.object(c, "PeerAPI", return_value=api):
            result = c.run("qwen", {"PLENUM_APC_QWEN_KEY": "x" * 32},
                           lambda kind, text, env: "Answer")
        self.assertEqual(result["processed"], 1)
        self.assertEqual(len(api.sent), 1)
        self.assertIn("msg_123", api.sent[0][1])
        self.assertEqual(len(api.acked), 1)

    def test_recovery_does_not_rerun_model(self):
        m = {"id": "msg_123", "thread_id": THREAD,
             "sender_id": OWNER, "type": "text", "content": "What is an idea?"}
        api = FakeAPI([m], replied=True)
        with patch.object(c, "PeerAPI", return_value=api):
            result = c.run("qwen", {"PLENUM_APC_QWEN_KEY": "x" * 32},
                           lambda *args: self.fail("duplicate model invocation"))
        self.assertEqual(result["processed"], 1)
        self.assertEqual(len(api.sent), 0)
        self.assertEqual(len(api.acked), 1)


if __name__ == "__main__":
    unittest.main()
