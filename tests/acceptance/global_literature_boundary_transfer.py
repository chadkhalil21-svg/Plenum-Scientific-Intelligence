"""Frozen prospective acceptance: public global literature response boundary."""
import io
import unittest
from unittest.mock import patch
from urllib.request import HTTPRedirectHandler
from plenum_ai.global_sources import _get, arxiv_query_url, MAX_BYTES

class Response(io.BytesIO):
    def __init__(self, body=b"metadata", **fields):
        super().__init__(body)
        self.read_calls = 0
        for key, value in fields.items():
            setattr(self, key, value)
    def read(self, *args):
        self.read_calls += 1
        return super().read(*args)

class GlobalBoundaryAcceptance(unittest.TestCase):
    def test_reject_response_before_read(self):
        url = arxiv_query_url("photon research")
        cases = (
            {"status": 503, "url": url},
            {"status": 200, "url": "https://example.com/elsewhere"},
            {"status": 200, "geturl": lambda: "https://example.com/elsewhere"},
            {"status": 200, "url": url, "geturl": lambda: "https://example.com/elsewhere"},
        )
        for fields in cases:
            with self.subTest(fields=fields):
                response = Response(**fields)
                with self.assertRaises(ValueError):
                    _get(url, opener=lambda *a, **k: response)
                self.assertEqual(response.read_calls, 0)

    def test_preserve_valid_and_refuse_default_redirects(self):
        url = arxiv_query_url("photon research")
        for fields in ({}, {"status": 200, "url": url},
                       {"status": 200, "geturl": lambda: url}):
            with self.subTest(fields=fields):
                response = Response(**fields)
                self.assertEqual(_get(url, opener=lambda *a, **k: response), b"metadata")
                self.assertEqual(response.read_calls, 1)
        with self.assertRaises(ValueError):
            _get(url, opener=lambda *a, **k: Response(b"x" * (MAX_BYTES + 1)))
        response = Response(status=200, url=url)
        def fake_build(*handlers):
            self.assertTrue(any(isinstance(h, HTTPRedirectHandler) or
                                (isinstance(h, type) and issubclass(h, HTTPRedirectHandler))
                                for h in handlers))
            from types import SimpleNamespace
            for handler in handlers:
                h = handler() if isinstance(handler, type) else handler
                if isinstance(h, HTTPRedirectHandler):
                    self.assertIsNone(h.redirect_request(None, None, 302, "", {}, "https://example.com/"))
            return SimpleNamespace(open=lambda *a, **k: response)
        with patch("urllib.request.build_opener", side_effect=fake_build) as builder:
            self.assertEqual(_get(url), b"metadata")
            self.assertEqual(builder.call_count, 1)
