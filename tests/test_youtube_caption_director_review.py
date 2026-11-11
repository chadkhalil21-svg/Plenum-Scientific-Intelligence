"""Focused free public-caption three-director contract; no external requests."""
import copy
import unittest
from plenum_ai import youtube_caption_director_review as d
from plenum_ai import youtube_public_caption_worker as r

ID = "VR35PxCFZIQ"


def founder(ids=(ID,)):
    return {"action": "opened", "repository": {"full_name": r.REPO},
            "issue": {"number": 900, "title": r.TITLE, "user": {"login": r.OWNER},
                      "body": r.MARKER + "\nvideos: " + ",".join(ids)}}


def rows(video_id):
    return [{"start": float(i * 4), "text": "Gamma presentation and Napkin AI diagram"}
            for i in range(12)]


class ThreeDirectorTests(unittest.TestCase):
    def test_real_founder_scope_and_unreviewed_video_rejected(self):
        self.assertEqual(d.read_founder_task(founder()), (900, [ID]))
        for event in (founder(("dQw4w9WgXcQ",)), founder((ID, ID)),
                      {**founder(), "action": "edited"}):
            with self.assertRaises((PermissionError, ValueError)):
                d.read_founder_task(event)

    def test_three_roles_reuse_original_worker_and_do_not_claim_independent_source_read(self):
        catalog = r.load_catalog()
        report = r.research([ID], catalog, fetch=rows)
        engineer = d.engineering_diagnosis(report, [ID])
        result = d.audit(report, engineer, [ID], catalog)
        self.assertTrue(engineer["existing_worker_integrated"])
        self.assertEqual(result["retrieved"], 1)
        self.assertEqual(result["status"], "PARTIAL_UNCONFIRMED_SOURCE")
        self.assertEqual(result["evidence_integrity"], "PASS_BOUNDED_SCHEMA")
        self.assertFalse(result["independent_original_caption_retrieval"])

    def test_true_provider_block_is_reported_blocked_not_completed(self):
        def blocked(video_id):
            raise OSError("public YouTube cloud blocked")
        catalog = r.load_catalog()
        report = r.research([ID], catalog, fetch=blocked)
        engineer = d.engineering_diagnosis(report, [ID])
        result = d.audit(report, engineer, [ID], catalog)
        self.assertEqual(result["retrieved"], 0)
        self.assertEqual(result["status"], "BLOCKED_UPSTREAM_CAPTIONS")
        self.assertEqual(result["next_owner"], "Engineering Director")
        self.assertEqual(engineer["status"], "SOURCE_OR_PROVIDER_BLOCKED")

    def test_fail_closed_on_invented_segment_or_timecode_or_engineering_claim(self):
        catalog = r.load_catalog()
        report = r.research([ID], catalog, fetch=rows)
        engineer = d.engineering_diagnosis(report, [ID])
        cases = []
        modified = copy.deepcopy(report)
        modified["outcomes"][0]["caption_segments_count"] = 1
        cases.append((modified, engineer))
        modified = copy.deepcopy(report)
        modified["outcomes"][0]["platforms"][0]["timestamps_seconds"] = [999999]
        cases.append((modified, engineer))
        altered_eng = copy.deepcopy(engineer)
        altered_eng["videos_retrieved_reported_not_independently_certified"] = 0
        cases.append((report, altered_eng))
        for evidence, handoff in cases:
            self.assertEqual(d.audit(evidence, handoff, [ID], catalog)["status"], "REJECTED_EVIDENCE")
        self.assertEqual(d.audit(None, None, [ID], catalog)["status"], "REJECTED_EVIDENCE")

    def test_direct_failure_then_fallback_failure_is_reported_without_secret_text(self):
        video = r.load_catalog()[ID]
        def blocked(_): raise OSError("blocked secret")
        def fallblocked(_): raise TimeoutError("provider secret")
        result = r.review_video(video, fetch=blocked, fallback=fallblocked)
        self.assertFalse(result["captions_read"])
        self.assertTrue(result["fallback_attempted"])
        self.assertEqual(result["fallback_failure_type"], "TimeoutError")
        self.assertEqual(result["failure_type"], "TimeoutError")
        self.assertNotIn("provider secret", str(result))


if __name__ == "__main__":
    unittest.main()
