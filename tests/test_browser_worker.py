"""Safe browser boundary and real Playwright local interaction tests."""
import asyncio
import importlib.util
import unittest
from plenum_ai.browser_worker import (
    allowed_public_url, test_local_interaction, public_link_target, validate_public_links,
)

class BrowserPolicy(unittest.TestCase):
    def test_strict_public_domain_allowlist(self):
        for url in [
            "https://example.com/",
            "https://english.cas.cn/newsroom/",
            "https://science.nasa.gov/news/",
            "https://arxiv.org/list/physics/recent",
        ]:
            self.assertTrue(allowed_public_url(url), url)
        for url in [
            "file:///etc/passwd", "http://example.com/", "https://127.0.0.1/",
            "https://localhost/", "https://169.254.169.254/latest/",
            "https://example.com.evil.com/", "https://user:password@example.com/",
            "https://example.com:8080/path", "https://example.com/#token",
            "https://www.bank.com/", "https://nasa.gov/", "https://evil.example/",
            "https://example.com/\nHeader:malicious",
        ]:
            self.assertFalse(allowed_public_url(url), url)

    def test_public_link_navigation_only_allows_safe_links(self):
        self.assertEqual(validate_public_links(["Research", "Next"]), ("Research", "Next"))
        self.assertEqual(public_link_target("https://example.com/start",
            "/research"), "https://example.com/research")
        for href in (
            "javascript:alert(1)", "file:///etc/passwd", "//evil.com/x",
            "https://127.0.0.1/private", "/logout?token=hidden",
            "/about#fragment", "https://example.com.evil.net/", "",
        ):
            with self.subTest(href=href):
                with self.assertRaises(PermissionError):
                    public_link_target("https://example.com/start", href)
        for links in (["x"] * 4, ["line\nfeed"], [""], [" x "], "Link"):
            with self.subTest(links=links):
                with self.assertRaises(ValueError):
                    validate_public_links(links)

    @unittest.skipUnless(importlib.util.find_spec("playwright") is not None,
                         "Dedicated isolated browser workflow installs official Playwright")
    def test_real_browser_click_and_text_entry_no_network(self):
        report = asyncio.run(test_local_interaction())
        self.assertTrue(report["actual_chromium_input_and_click_verified"])
        self.assertEqual(report["remote_network_requests"], 0)
        self.assertFalse(report["website_modified"])
        self.assertFalse(report["AGI_demonstrated"])

if __name__ == "__main__":
    unittest.main()
