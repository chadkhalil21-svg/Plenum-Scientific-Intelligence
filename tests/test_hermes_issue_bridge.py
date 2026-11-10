"""Only new Hermes GitHub adapter; no additional model or browser benchmark."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from plenum_ai.hermes_issue_bridge import create_public_assignment, read_public_assignment

URL="https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/"
OBJECTIVE="Create a public data validator for scientific observations"

class Response:
    def __init__(self,obj,status=200):self.obj=obj;self.status=status
    def __enter__(self):return self
    def __exit__(self,*a):return False
    def read(self,n):return json.dumps(self.obj).encode()

class FakeClient:
    def __init__(self,actor="chadkhalil21-svg"):self.actor=actor;self.calls=[]
    def open(self,request,timeout):
        self.calls.append((request.get_method(),request.full_url,request.data))
        if request.full_url.endswith("/user"):
            return Response({"login":self.actor})
        if request.get_method()=="POST":
            return Response({"number":456,"html_url":URL+"456"},status=201)
        if "/comments?" in request.full_url:
            return Response([
                {"user":{"login":"outsider"},"body":"Status: **DRAFT_READY_FOR_FOUNDER**"},
                {"user":{"login":"github-actions[bot]"},
                 "body":"<!-- plenum-public-workforce-run:123 -->\nStatus: **DRAFT_READY_FOR_FOUNDER**."}
            ])
        raise AssertionError("Unexpected provider endpoint")

class PublicHermesBridgeTests(unittest.TestCase):
    def test_known_public_request_creates_one_exact_owner_issue(self):
        client=FakeClient()
        x=create_public_assignment("public_program",OBJECTIVE,token="private-in-test",opener=client)
        self.assertEqual(x["issue_url"],URL+"456")
        self.assertEqual(x["state"],"FOUNDER_PUBLIC_ISSUE_CREATED")
        self.assertEqual(len(client.calls),2)
        self.assertEqual([z[0] for z in client.calls],["GET","POST"])
        body=json.loads(client.calls[-1][2])
        self.assertEqual(body["title"],"[Plenum Workforce] public research")
        self.assertTrue(body["body"].startswith("PLENUM_PUBLIC_WORKFORCE_V2\nkind: public_program"))
        self.assertNotIn("private-in-test",x["issue_url"])

    def test_wrong_owner_token_never_sends_write(self):
        client=FakeClient(actor="outsider")
        with self.assertRaises(PermissionError):
            create_public_assignment("public_program",OBJECTIVE,token="scoped",opener=client)
        self.assertEqual(len(client.calls),1)

    def test_private_tasks_refused_before_identity_or_http_call(self):
        c=FakeClient()
        for kind,objective in (
            ("send_email",OBJECTIVE),("public_program","Read confidential password files"),
            ("public_program","short")
        ):
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                create_public_assignment(kind,objective,token="abc",opener=c)
        self.assertEqual(len(c.calls),0)

    def test_readback_does_not_expose_issues_or_third_party_comments(self):
        c=FakeClient()
        result=read_public_assignment(456,token="abc",opener=c)
        self.assertEqual(result["status"],"DRAFT_READY_FOR_FOUNDER")
        self.assertFalse(result["private_or_full_issue_content_returned"])
        self.assertEqual([x[0] for x in c.calls],["GET","GET"])

    def test_hermes_plugin_registers_exact_two_bounded_tools(self):
        root=Path(__file__).resolve().parents[1]/"integrations/hermes/plugins/plenum-public-workforce"
        spec=importlib.util.spec_from_file_location("plenum_hermes_plugin",root/"__init__.py")
        plugin=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugin)
        class Context:
            def __init__(self):self.tools=[]
            def register_tool(self,**kw):self.tools.append(kw)
        ctx=Context();plugin.register(ctx)
        self.assertEqual({t["name"] for t in ctx.tools},
                         {"plenum_assign_public_task","plenum_read_public_task_status"})
        self.assertTrue(all("schema" in t and "handler" in t for t in ctx.tools))

if __name__=="__main__":
    unittest.main()
