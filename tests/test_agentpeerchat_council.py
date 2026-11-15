import unittest
from unittest.mock import patch
from plenum_ai import agentpeerchat_council as c

OWNER, QWEN, GEMINI, LLAMA, THREAD = "hum_owner", "agt_qwen", "agt_gemini", "agt_llama", "thr_1234567890"


class FakeAPI:
    def __init__(self, incoming, own=QWEN, replied=False):
        self.incoming, self.own, self.replied = incoming, own, replied
        self.sent, self.acked = [], []
        self.thread_members = None
        self.principals = [
            {"id": OWNER, "kind": "owner", "active": 1, "name": "Founder"},
            {"id": QWEN, "kind": "agent", "active": 1, "name": c.AGENTS["qwen"]},
            {"id": GEMINI, "kind": "agent", "active": 1, "name": c.AGENTS["gemini"]},
            {"id": LLAMA, "kind": "agent", "active": 1, "name": c.AGENTS["llama"]},
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
            return {"thread": {"title": c.TITLE, "members": (
                self.principals if self.thread_members is None else self.thread_members)},
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

    def test_llama_supported_in_public_council(self):
        self.assertEqual(c.AGENTS["llama"], "Plenum Prometheus — Llama")
        self.assertEqual(c.config("llama", {"PLENUM_APC_LLAMA_KEY": "x" * 32})[1],
                         "x" * 32)
        msg = {"type": "text", "sender_id": OWNER, "content": "Compare materials"}
        self.assertEqual(c.classify(msg, "llama", {OWNER: {"kind": "owner"}}, LLAMA),
                         ("initial", "Compare materials"))

    def test_three_agent_peers_are_bounded_to_initial_messages(self):
        peer = {
            GEMINI: {"kind": "agent", "name": c.AGENTS["gemini"]},
            LLAMA: {"kind": "agent", "name": c.AGENTS["llama"]},
            QWEN: {"kind": "agent", "name": c.AGENTS["qwen"]},
        }
        for source_model, sender in (("gemini", GEMINI), ("llama", LLAMA)):
            m = {"type": "text", "sender_id": sender,
                 "content": c.MARKERS[source_model] + "\nProposed approach"}
            self.assertEqual(c.classify(m, "qwen", peer, QWEN),
                             ("critique", "Proposed approach"))
            m["content"] = c.CRITIQUE[source_model] + "\nAssessment"
            self.assertIsNone(c.classify(m, "qwen", peer, QWEN))
        own = {"type": "text", "sender_id": LLAMA,
               "content": c.MARKERS["llama"] + "\nMy answer"}
        self.assertIsNone(c.classify(own, "llama", peer, LLAMA))

    def test_owner_member_required(self):
        api = FakeAPI([])
        self.assertIn(OWNER, c.members_for(api, THREAD))
        api.principals = api.principals[1:]
        self.assertIsNone(c.members_for(api, THREAD))

    def test_only_real_active_group_members_can_issue_model_tasks(self):
        outsider = {"id": "agt_other", "kind": "agent", "active": 1,
                    "name": c.AGENTS["gemini"]}
        api = FakeAPI([])
        api.principals.append(outsider)
        api.thread_members = api.principals[:3]
        members = c.members_for(api, THREAD)
        self.assertIn(OWNER, members)
        self.assertIn(QWEN, members)
        self.assertNotIn("agt_other", members)
        self.assertIsNone(c.classify(
            {"type": "text", "sender_id": "agt_other",
             "content": c.MARKERS["gemini"] + " unsolicited idea"},
            "qwen", members, QWEN,
        ))

    def test_nonmember_agent_must_not_model_or_ack_owner_messages(self):
        msg = {"id": "msg_123", "thread_id": THREAD, "sender_id": OWNER,
               "type": "text", "content": "Public idea"}
        api = FakeAPI([msg])
        api.thread_members = [api.principals[0], api.principals[2]]
        with patch.object(c, "PeerAPI", return_value=api):
            result = c.run("qwen", {"PLENUM_APC_QWEN_KEY": "x" * 32},
                           lambda *args: self.fail("nonmember model invoked"))
        self.assertEqual(result["processed"], 0)
        self.assertEqual(api.sent, [])
        self.assertEqual(api.acked, [])

    def test_malformed_thread_member_ids_are_ignored(self):
        api = FakeAPI([])
        api.thread_members = [api.principals[0], {"id": ["invalid"]}, None]
        members = c.members_for(api, THREAD)
        self.assertEqual(set(members), {OWNER})

    def test_upstream_cursor_pages_reach_owner_message_beyond_first_twenty(self):
        class PagedAPI(FakeAPI):
            def __init__(self, incoming):
                super().__init__(incoming)
                self.inbox_paths = []
            def request(self, path, payload=None, idempotency=None, method=None):
                if path.startswith("/inbox?"):
                    self.inbox_paths.append(path)
                    after = int(path.split("after=")[1].split("&")[0])
                    items = [m for m in self.incoming if m["seq"] > after][:20]
                    return {"items": items, "next_cursor": str(items[-1]["seq"]),
                            "has_more": any(m["seq"] > items[-1]["seq"]
                                            for m in self.incoming)}
                return super().request(path, payload=payload,
                                       idempotency=idempotency, method=method)
        unrelated = [
            {"id": "msg_" + str(i), "seq": i, "thread_id": THREAD,
             "sender_id": OWNER, "type": "reaction", "content": "not a task"}
            for i in range(1, 21)
        ]
        older_owner = {"id": "msg_21", "seq": 21, "thread_id": THREAD,
                       "sender_id": OWNER, "type": "text",
                       "content": "Describe one useful public Terra result"}
        api = PagedAPI(unrelated + [older_owner])
        with patch.object(c, "PeerAPI", return_value=api):
            result = c.run("qwen", {"PLENUM_APC_QWEN_KEY": "x" * 32},
                           lambda kind, source, env: "Evidence-first draft")
        self.assertEqual(result["processed"], 1)
        self.assertEqual(api.inbox_paths,
                         ["/inbox?after=0&limit=20",
                          "/inbox?after=20&limit=20"])
        self.assertEqual(len(api.sent), 1)
        self.assertEqual(api.sent[0][0]["reply_to"], "msg_21")
        self.assertEqual(api.acked, ["/messages/msg_21/ack"])

    def test_many_unacked_owner_questions_are_bounded_per_inference_sweep(self):
        class ManyAPI(FakeAPI):
            def request(self, path, payload=None, idempotency=None, method=None):
                if path.startswith("/inbox?"):
                    return {"items": self.incoming[:20], "next_cursor": "20",
                            "has_more": True}
                return super().request(path, payload, idempotency, method)
        items = [{"id": "msg_" + str(i), "thread_id": THREAD,
                  "sender_id": OWNER, "type": "text",
                  "content": "Public question " + str(i)}
                 for i in range(1, 21)]
        api = ManyAPI(items)
        with patch.object(c, "PeerAPI", return_value=api):
            result = c.run("qwen", {"PLENUM_APC_QWEN_KEY": "x" * 32},
                           lambda kind, source, env: "Reviewed answer")
        self.assertEqual(result["processed"], c.MAX_ACTIONABLE_PER_SWEEP)
        self.assertEqual(len(api.sent), c.MAX_ACTIONABLE_PER_SWEEP)
        self.assertEqual(len(api.acked), c.MAX_ACTIONABLE_PER_SWEEP)

    def test_invalid_upstream_page_cursor_fails_closed(self):
        class StalledAPI(FakeAPI):
            def request(self, path, payload=None, idempotency=None, method=None):
                if path.startswith("/inbox?"):
                    return {"items": [], "next_cursor": "0",
                            "has_more": True}
                return super().request(path, payload, idempotency, method)
        with patch.object(c, "PeerAPI", return_value=StalledAPI([])):
            with self.assertRaisesRegex(RuntimeError, "stalled_inbox_cursor"):
                c.inspect("qwen", {"PLENUM_APC_QWEN_KEY": "x" * 32})

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


class ClaudeBridgeTests(unittest.TestCase):
    def test_claude_identity_and_access_config(self):
        self.assertEqual(c.config("claude", {"PLENUM_APC_CLAUDE_KEY": "x"*32})[1], "x"*32)
        self.assertEqual(c.classify({"type":"text","sender_id":OWNER,"content":"Council question"},
                 "claude",{OWNER:{"kind":"owner"}},"agt_claude"),("initial","Council question"))
    def test_claude_requires_provider_credential(self):
        with self.assertRaisesRegex(RuntimeError,"missing_puter_token"):
            c.claude_answer("initial","Hello",{})
    def test_claude_short_reply_budget_not_consumed_by_default_thinking(self):
        native_run = c.subprocess.run
        def simulate_provider(args, **kwargs):
            # Haiku 5.5 defaults to thinking, which counts toward max_tokens.
            script = args[2].replace("const { init } = require('@heyputer/puter.js/src/init.cjs');",
                "const init = () => ({ai:{chat:async (_messages, opts) => opts.thinking?.type === 'disabled' ? {message:{content:'Independent answer'},finish_reason:'stop'} : {message:{content:'',reasoning:'thinking'},finish_reason:'length'}}});")
            return native_run([args[0], args[1], script], **kwargs)
        with patch.object(c.subprocess, 'run', side_effect=simulate_provider):
            self.assertEqual(c.claude_answer('initial', 'Question', {'PLENUM_PUTER_TOKEN':'test'}), 'Independent answer')
    def test_claude_sdk_call_is_bounded_and_isolates_credentials(self):
        with patch.object(c.subprocess, "run", return_value=c.subprocess.CompletedProcess(
                ["node"], 0, stdout='{"answer":"Independent answer"}', stderr='')) as call:
            self.assertEqual(c.claude_answer("initial", "Question", {
                "PLENUM_PUTER_TOKEN": "test-token", "PLENUM_APC_CLAUDE_KEY": "private-key"}),
                "Independent answer")
        args, kw = call.call_args
        self.assertIn("anthropic/claude-haiku-5-5", args[0][2])
        self.assertIn("refusalFallback: false", args[0][2])
        self.assertNotIn("PLENUM_APC_CLAUDE_KEY", kw["env"])
        self.assertNotIn("test-token", str(args))
    def test_claude_peer_can_be_criticized_once(self):
        member={"agt_claude":{"kind":"agent","name":"Plenum Prometheus — Claude"}}
        msg={"type":"text","sender_id":"agt_claude","content":"[Claude | initial]\nA claim"}
        self.assertEqual(c.classify(msg,"qwen",member,QWEN),("critique","A claim"))
        msg["content"]="[Claude | critique]\nA claim"
        self.assertIsNone(c.classify(msg,"qwen",member,QWEN))


class ComputerBridgeTests(unittest.TestCase):
    def test_puter_worker_exits_after_answer_despite_open_sdk_handles(self):
        native_run = c.subprocess.run
        def run_with_open_handle(args, **kwargs):
            script = args[2].replace("const { init } = require('@heyputer/puter.js/src/init.cjs');",
                "const init = () => { setInterval(() => {}, 100); return {ai:{chat:async () => ({message:{content:'Answer'}})}}; };")
            kwargs['timeout'] = 2
            return native_run([args[0], args[1], script], **kwargs)
        with patch.object(c.subprocess, 'run', side_effect=run_with_open_handle):
            self.assertEqual(c.computer_answer('initial', 'Question', {'PLENUM_PUTER_TOKEN':'test'}), 'Answer')

    def test_computer_identity_and_genuine_gpt_provider(self):
        self.assertEqual(c.AGENTS["computer"], "Plenum Prometheus — Computer")
        self.assertEqual(c.config("computer", {"PLENUM_APC_COMPUTER_KEY": "x"*32})[1], "x"*32)
        with patch.object(c.subprocess, "run", return_value=c.subprocess.CompletedProcess(
                ["node"], 0, stdout='{"answer":"Independent answer"}', stderr='')) as call:
            self.assertEqual(c.computer_answer("initial", "Question", {
                "PLENUM_PUTER_TOKEN": "test-token", "PLENUM_APC_COMPUTER_KEY": "private-key"}),
                "Independent answer")
        args, kw = call.call_args
        self.assertIn("openai/gpt-5.4-nano", args[0][2])
        self.assertIn("refusalFallback: false", args[0][2])
        self.assertNotIn("PLENUM_APC_COMPUTER_KEY", kw["env"])
        member = {"agt_computer":{"kind":"agent","name":c.AGENTS["computer"]}}
        msg = {"type":"text","sender_id":"agt_computer","content":"[Computer | initial]\nA claim"}
        self.assertEqual(c.classify(msg,"qwen",member,QWEN),("critique","A claim"))


if __name__ == "__main__":
    unittest.main()
