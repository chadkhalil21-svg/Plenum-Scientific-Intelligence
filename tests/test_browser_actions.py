"""Offline bounded multi-action Playwright execution."""
import asyncio
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

from services.computer_browser.browser_actions import (
    BrowserStep, validate_steps, _approved_upload, execute_steps_on_page,
)

from services.computer_browser.owner_task_loop import execute_owner_adaptive_loop

HAS_BROWSER=importlib.util.find_spec("playwright") is not None


class BrowserActionContractTests(unittest.TestCase):
    def test_whitelist_and_bounded_plan(self):
        self.assertTrue(validate_steps([BrowserStep("fill","#title","A")]))
        for steps in (
            [],
            [BrowserStep("fill","#x","long")]*21,
            [BrowserStep("javascript","window.alert('x')")],
            [BrowserStep("click","")],
            [BrowserStep("upload","#file",file_id="../../etc/passwd")],
            [BrowserStep("click","#button",file_id="unapproved")],
            [BrowserStep("fill","#text","A"*5000)],
        ):
            with self.subTest(steps=str(steps)[:45]):
                with self.assertRaises((PermissionError,ValueError)):
                    validate_steps(steps)

    def test_upload_paths_are_confined_and_small(self):
        with tempfile.TemporaryDirectory() as root:
            base=Path(root)
            (base/"approved.txt").write_text("approved, synthetic")
            self.assertEqual(_approved_upload(root,"approved.txt"),str(base/"approved.txt"))
            with self.assertRaises((PermissionError,FileNotFoundError)):
                _approved_upload(root,"../other.txt")
            (base/"big.bin").write_bytes(b"0"*(8*1024*1024+1))
            with self.assertRaises(ValueError):
                _approved_upload(root,"big.bin")

    def test_unscoped_external_page_never_runs(self):
        class StubPage:
            url="https://example.com/"
        async def no_scope():
            with self.assertRaises(PermissionError):
                await execute_steps_on_page(StubPage(),[BrowserStep("click","#button")])
        asyncio.run(no_scope())

    @unittest.skipUnless(HAS_BROWSER,"Dedicated CI includes Chromium")
    def test_actual_chromium_multistep_form(self):
        from services.computer_browser.browser_actions import test_real_local_task
        result=asyncio.run(test_real_local_task())
        self.assertTrue(result["real_chromium_form_fill_click_select_check_upload"])
        self.assertFalse(result["real_website_modified"])
        self.assertFalse(result["AGI_demonstrated"])



class AdaptiveOwnerLoopContractTests(unittest.TestCase):
    """Only new adapter behavior; no repeated external login or demo tests."""

    class FakeLocator:
        def __init__(self, page, selector):
            self.page, self.selector = page, selector

        async def count(self):
            return self.page.matches.get(self.selector, 0)

        async def click(self, **kwargs):
            self.page.clicks.append(self.selector)
            if self.page.fail_after_click:
                raise TimeoutError("DO NOT PRINT PRIVATE DOM")

    class FakePage:
        url = "https://example.com/owner"
        def __init__(self, matches=None, fail_after_click=False):
            self.matches = matches or {"#ready": 1}
            self.clicks = []
            self.fail_after_click = fail_after_click

        def locator(self, selector):
            return AdaptiveOwnerLoopContractTests.FakeLocator(self, selector)

    def test_missing_selector_replans_without_executing(self):
        async def run():
            page = self.FakePage()
            candidates = iter([BrowserStep("click", "#missing"),
                               BrowserStep("click", "#ready")])
            events = []
            async def observe(p):
                return {"ready": True}
            async def decide(obs, feedback):
                if len(events) > 0:
                    self.assertEqual(feedback, "locator_missing")
                return next(candidates)
            async def consent(step):
                self.assertEqual(step.selector, "#ready")
                return True
            async def verify(p):
                return p.clicks == ["#ready"]
            async def progress(event):
                events.append(event)
            result = await execute_owner_adaptive_loop(
                page, authorized_origins={"https://example.com"},
                observe=observe, decide=decide, consent=consent,
                verify=verify, progress=progress)
            self.assertEqual(result["status"], "CALLER_VERIFIED")
            self.assertEqual(result["executed_steps"], 1)
            self.assertEqual(result["safe_locator_replans"], 1)
            self.assertFalse(result["private_page_text_or_credentials_returned"])
            self.assertTrue(all(set(e) == {"state", "step"} for e in events))
        asyncio.run(run())

    def test_delayed_link_observation_recovers_without_click_retry(self):
        async def run():
            page = self.FakePage()
            polls = []
            async def observe(current):
                polls.append(len(current.clicks))
                return {"ready": len(polls) >= 2}
            def decide(view, feedback):
                return (BrowserStep("click", "#ready")
                        if view["ready"] else None)
            recovered = []
            async def passive(current, feedback):
                recovered.append(feedback)
                return True  # Only a new observation, not a page action.
            result = await execute_owner_adaptive_loop(
                page, authorized_origins={"https://example.com"},
                observe=observe, decide=decide,
                consent=lambda step: step.selector == "#ready",
                confirm_step=lambda p, step: p.clicks == ["#ready"],
                verify=lambda p: p.clicks == ["#ready"],
                recover_observation=passive,
            )
            self.assertEqual(result["status"], "CALLER_VERIFIED")
            self.assertEqual(result["executed_steps"], 1)
            self.assertEqual(result["safe_locator_replans"], 1)
            self.assertEqual(page.clicks, ["#ready"])
            self.assertEqual(len(recovered), 1)
        asyncio.run(run())

    def test_unverified_postclick_blocks_before_second_action(self):
        async def run():
            page = self.FakePage()
            checked = []
            result = await execute_owner_adaptive_loop(
                page, authorized_origins={"https://example.com"},
                observe=lambda p: {"ready": True},
                decide=lambda obs, feedback: BrowserStep("click", "#ready"),
                consent=lambda step: True,
                confirm_step=lambda p, step: False,
                verify=lambda p: checked.append(1) or False,
            )
            self.assertEqual(result["status"],
                             "BLOCKED_POST_ACTION_UNVERIFIED_NO_RETRY")
            self.assertEqual(result["executed_steps"], 1)
            self.assertEqual(page.clicks, ["#ready"])
            self.assertEqual(checked, [])
            self.assertFalse(result["automatic_write_retries"])
        asyncio.run(run())

    def test_no_candidate_recovery_is_strictly_bounded(self):
        async def run():
            page = self.FakePage()
            rechecked = []
            result = await execute_owner_adaptive_loop(
                page, authorized_origins={"https://example.com"},
                observe=lambda p: [],
                decide=lambda obs, feedback: None,
                consent=lambda step: True,
                verify=lambda p: False,
                recover_observation=lambda p, feedback:
                    rechecked.append(feedback) or True,
            )
            self.assertEqual(result["status"], "BLOCKED_NO_NEXT_STEP")
            self.assertEqual(result["safe_locator_replans"], 2)
            self.assertEqual(len(rechecked), 2)
            self.assertEqual(page.clicks, [])
            with self.assertRaises(PermissionError):
                await execute_owner_adaptive_loop(
                    page, authorized_origins={"https://example.com"},
                    observe=lambda p: [],
                    decide=lambda o, f: None,
                    consent=lambda step: True,
                    verify=lambda p: False,
                    recover_observation=lambda p, f: "yes",
                )
        asyncio.run(run())

    def test_missing_consent_never_clicks(self):
        async def run():
            page = self.FakePage()
            with self.assertRaises(PermissionError):
                await execute_owner_adaptive_loop(
                    page, authorized_origins={"https://example.com"},
                    observe=lambda p: {},
                    decide=lambda o, feedback: BrowserStep("click", "#ready"),
                    consent=lambda step: False,
                    verify=lambda p: True)
            self.assertEqual(page.clicks, [])
        asyncio.run(run())

    def test_uncertain_click_is_not_retried(self):
        async def run():
            page = self.FakePage(fail_after_click=True)
            result = await execute_owner_adaptive_loop(
                page, authorized_origins={"https://example.com"},
                observe=lambda p: {},
                decide=lambda o, feedback: BrowserStep("click", "#ready"),
                consent=lambda step: True,
                verify=lambda p: False)
            self.assertEqual(result["status"], "BLOCKED_UNCERTAIN_ACTION_NO_RETRY")
            self.assertEqual(page.clicks, ["#ready"])
            self.assertEqual(result["executed_steps"], 0)
        asyncio.run(run())

    def test_ambiguous_target_and_bad_origin_block(self):
        async def run():
            page = self.FakePage(matches={"#ready": 2})
            result = await execute_owner_adaptive_loop(
                page, authorized_origins={"https://example.com"},
                observe=lambda p: {}, decide=lambda o, f: BrowserStep("click", "#ready"),
                consent=lambda step: True, verify=lambda p: False)
            self.assertEqual(result["status"], "BLOCKED_AMBIGUOUS_OR_MISSING_LOCATOR")
            self.assertEqual(page.clicks, [])
            with self.assertRaises(PermissionError):
                await execute_owner_adaptive_loop(
                    page, authorized_origins={"https://other.example.org"},
                    observe=lambda p: {}, decide=lambda o, f: None,
                    consent=lambda step: True, verify=lambda p: False)
        asyncio.run(run())

if __name__=="__main__":
    unittest.main()
