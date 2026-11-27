"""Prospective bounded health response recovery acceptance; no network."""
import io
import unittest
from plenum_ai.business_public_watch import TARGETS, probe, inspect_target

class Reply(io.BytesIO):
    status = 200
    headers = {"Content-Type": "application/json"}

class Client:
    def __init__(self, payload):
        self.payload = payload
    def open(self, request, timeout):
        return Reply(self.payload)

GOOD = b'{"service":"american-rider-server"}'
DEEP = b'{"service":"american-rider-server","extra":' + b'[' * 10000 + b'0' + b']' * 10000 + b'}'

class PublicHealthNestedJsonAcceptance(unittest.TestCase):
    def test_nested_response_is_bounded_failure(self):
        self.assertLess(len(DEEP), 65536)
        self.assertEqual(probe(TARGETS[2], opener=Client(DEEP)), (False, "unexpected_content", None))

    def test_normal_and_wrong_service(self):
        self.assertEqual(probe(TARGETS[2], opener=Client(GOOD)), (True, "verified_read", 200))
        self.assertEqual(probe(TARGETS[2], opener=Client(b'{"service":"wrong"}')), (False, "unexpected_service", 200))
        self.assertEqual(probe(TARGETS[2], opener=Client(GOOD+b' '*65536)), (False, "unexpected_content", 200))

    def test_existing_retry_recovers_without_replaying_success(self):
        bodies = iter((DEEP, GOOD, GOOD))
        pauses = []
        result = inspect_target(TARGETS[2], probe_fn=lambda t: probe(t, opener=Client(next(bodies))),
                                sleep_fn=pauses.append, max_attempts=2)
        self.assertEqual(result["status"], "PUBLIC_HTTP_VERIFIED")
        self.assertEqual(result["attempts"], 3)
        self.assertEqual(result["independent_gets"], 2)
        self.assertEqual(pauses, [1])
        self.assertFalse(result["external_actions_executed"])
