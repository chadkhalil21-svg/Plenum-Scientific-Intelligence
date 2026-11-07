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

if __name__=="__main__":
    unittest.main()
