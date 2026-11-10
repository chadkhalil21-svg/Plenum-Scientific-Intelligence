"""Only new Telegram status adapter and Hermes roster contracts; no model reruns."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from plenum_ai.telegram_workforce_status import build_notice, send_notice

PROJECT = Path(__file__).resolve().parents[1]
HERMES_DIR = PROJECT / "integrations" / "hermes"

def valid():
    return {"kind": "public_program", "status": "DRAFT_READY_FOR_FOUNDER",
            "issue_number": 347,
            "objective": "This confidential text must never enter a group chat"}

class TelegramAndHermesIntegrationTests(unittest.TestCase):
    def test_only_public_status_and_verified_issue_link_are_visible(self):
        message=build_notice(valid(),"42774323725")
        self.assertIn("/issues/347",message)
        self.assertIn("DRAFT_READY_FOR_FOUNDER",message)
        self.assertNotIn("confidential",message)
        self.assertNotIn("objective",message)
        self.assertLess(len(message),800)

    def test_reject_unknown_status_and_untrusted_issue(self):
        for changes in ({"kind":"send_private_email"},
                        {"status":"FULLY_AUTONOMOUS_SUCCESS"},
                        {"issue_number":"../../private"},
                        {"issue_number":-1}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                build_notice({**valid(),**changes},"42774323725")

    def test_no_unconfigured_chat_is_contacted(self):
        self.assertFalse(send_notice("Public status",bot_token="",chat_id=""))
        with self.assertRaises(ValueError):
            send_notice("Public",bot_token="leak",chat_id="-1001")

    def test_reporter_sends_one_bounded_message_using_owner_configured_bot(self):
        seen=[]
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,n): return b'{"ok":true,"result":{"message_id":123}}'
        def open_response(request,timeout):
            seen.append((request.full_url,request.data,timeout))
            return Response()
        token="12345678:"+"A"*35
        self.assertTrue(send_notice(build_notice(valid(),"42774323725"),
                                    bot_token=token,chat_id="-100123456789",
                                    opener=open_response))
        self.assertEqual(len(seen),1)
        data=json.loads(seen[0][1])
        self.assertEqual(data["chat_id"],"-100123456789")
        self.assertNotIn("confidential",data["text"])
        self.assertEqual(seen[0][2],12)

    def test_hermes_roster_is_not_an_installed_bot_or_account_grant(self):
        spec=importlib.util.spec_from_file_location(
            "hermes_provision",HERMES_DIR/"provision_profiles.py")
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        roster=module.inspect_roster()
        self.assertEqual(len(roster),10)
        self.assertIn("chief",roster)
        self.assertIn("verification",roster)
        with tempfile.TemporaryDirectory() as d:
            states=module.provision(roles=["chief","research","coding"],
                                    hermes_home=Path(d),apply=False)
            self.assertEqual(len(states),3)
            self.assertTrue(all(x.startswith("WOULD_CREATE") for x in states))
            self.assertFalse((Path(d)/"profiles").exists())
        self.assertIn("NOT a separate administrator",module.build_soul(roster["chief"]))

if __name__ == "__main__":
    unittest.main()
