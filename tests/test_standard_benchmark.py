"""No-download verification of reuse-first standard evaluation adapter."""
import copy
import json
import subprocess
import unittest
from plenum_ai import standard_benchmark as b

MODEL="Qwen/Qwen3-1.7B"


class StandardBenchmarkAdapterTests(unittest.TestCase):
    def test_reviewed_library_license_revision_and_release(self):
        r=b.registry()
        self.assertEqual(r["license"],"MIT")
        self.assertEqual(r["release"],"v0.4.13")
        self.assertEqual(len(r["commit"]),40)
        self.assertFalse(r["default_execution"])

    def test_default_plan_never_executes_or_promotes_models(self):
        p=b.plan(MODEL)
        self.assertEqual(p["sample_limit"],8)
        self.assertEqual(p["task"],"arc_easy")
        self.assertFalse(p["execution_authorized"])
        self.assertFalse(p["paid_remote_inference"])
        self.assertFalse(p["AGI_demonstrated"])
        self.assertIn("--device",p["command_argv"])
        self.assertIn("cpu",p["command_argv"])
        self.assertIn("--limit",p["command_argv"])
        self.assertIn("8",p["command_argv"])
        self.assertEqual(p["command_argv"][1:4],["-m","lm_eval","run"])

    def test_command_contains_immutable_checkpoint_revision(self):
        p=b.plan(MODEL,"hellaswag",6)
        x=p["command_argv"]
        self.assertIn("revision="+b.ALLOWED_MODELS[MODEL],x[x.index("--model_args")+1])
        self.assertEqual(x[x.index("--tasks")+1],"hellaswag")
        self.assertNotIn("--trust_remote_code",x)
        self.assertNotIn("--output_samples",x)

    def test_unsafe_task_model_and_unbounded_limits_fail_closed(self):
        for model,task,count in [
            ("Unknown/Model","arc_easy",8),
            (MODEL,"private_secret_benchmark",8),
            (MODEL,"arc_easy",10000),
            (MODEL,"arc_easy",0),
            (MODEL,"arc_easy",True),
            (MODEL,"arc_easy",1.5)]:
            with self.subTest(model=model,task=task,count=count),self.assertRaises(ValueError):
                b.plan(model,task,count)

    def test_explicit_execution_required(self):
        p=b.plan(MODEL)
        with self.assertRaises(PermissionError):
            b.execute(p,approved=False,installed_version="0.4.13",
                      runner=lambda *a,**kw:self.fail("No execution allowed"))

    def test_wrong_installed_library_version_fails_closed(self):
        p=b.plan(MODEL)
        with self.assertRaises(RuntimeError):
            b.execute(p,approved=True,installed_version="0.3.0",
                      runner=lambda *a,**kw:self.fail("Wrong package should not run"))

    def test_revised_or_malicious_execution_argv_rejected(self):
        p=b.plan(MODEL)
        tampered=copy.deepcopy(p)
        tampered["command_argv"]+=["--model_args","trust_remote_code=True"]
        with self.assertRaises(ValueError):
            b.execute(tampered,approved=True,installed_version="0.4.13",
                      runner=lambda *a,**kw:self.fail("Unauthorized command rejected"))
        p2=copy.deepcopy(p)
        p2["sample_limit"]=1000
        with self.assertRaises(ValueError):
            b.execute(p2,approved=True,installed_version="0.4.13",
                      runner=lambda *a,**kw:self.fail("Unbounded run rejected"))

    def test_explicit_manual_execution_is_bounded_and_shell_free(self):
        seen=[]
        def fake_run(argv,**kwargs):
            seen.append((argv,kwargs))
            return subprocess.CompletedProcess(argv,0)
        p=b.plan(MODEL,"arc_easy",4)
        report=b.execute(p,approved=True,installed_version="0.4.13",runner=fake_run)
        self.assertTrue(report["standard_framework_executed"])
        self.assertFalse(report["AGI_demonstrated"])
        self.assertFalse(report["automatic_model_promotion"])
        self.assertEqual(len(seen),1)
        self.assertEqual(seen[0][1]["timeout"],1200)
        self.assertTrue(seen[0][1]["check"])
        self.assertNotIn("shell",seen[0][1])

if __name__=="__main__":
    unittest.main()
