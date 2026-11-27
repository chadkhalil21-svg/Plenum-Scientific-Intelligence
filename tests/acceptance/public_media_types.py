"""Frozen prospective acceptance for exact endpoint media types, no network."""
import io
import unittest
from plenum_ai.business_public_watch import TARGETS, probe

class Reply(io.BytesIO):
    status = 200

class Client:
    def __init__(self, content_type):
        self.content_type = content_type
    def open(self, request, timeout):
        reply = Reply(b'{"service":"american-rider-server"}')
        reply.headers = {"Content-Type": self.content_type}
        return reply

class PublicMediaTypeAcceptance(unittest.TestCase):
    def test_exact_types_with_case_and_parameters(self):
        for target, types in ((TARGETS[2], ("application/json", "Application/JSON; charset=UTF-8")),
                              (TARGETS[0], ("text/html", "TEXT/HTML; charset=utf-8"))):
            for media_type in types:
                with self.subTest(target=target.name, media_type=media_type):
                    self.assertEqual(probe(target, opener=Client(media_type)), (True, "verified_read", 200))

    def test_misleading_substrings_and_parameter_values_are_not_types(self):
        for target, types in ((TARGETS[2], ("text/notjson", "application/jsonp", "text/plain; hint=json", "text/html")),
                              (TARGETS[0], ("application/nothtml", "text/htmlish", "text/plain; hint=html", "application/json"))):
            for media_type in types:
                with self.subTest(target=target.name, media_type=media_type):
                    self.assertEqual(probe(target, opener=Client(media_type)), (False, "unexpected_content_type", 200))
