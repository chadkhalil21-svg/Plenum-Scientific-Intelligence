"""The official YouTube API is optional and never leaks its API key."""
import io
import json
import unittest
from plenum_ai.youtube_api import video_search,from_environment

class HTTP(io.BytesIO):
    def __enter__(self):return self
    def __exit__(self,*args):self.close()


class YouTubeSearchTests(unittest.TestCase):
    def test_official_v3_search_and_sensitive_key_not_logged(self):
        token="owner-private-test-key-123456"
        raw=json.dumps({"items":[{
            "id":{"videoId":"AbCdEf12345"},
            "snippet":{"title":"A science lecture",
                       "channelTitle":"Research Lab",
                       "publishedAt":"2026-11-06T09:00:00Z"}
        }]}).encode()
        def fake(req,timeout):
            self.assertEqual(timeout,15)
            self.assertIn(token,req.full_url)
            self.assertIn("type=video",req.full_url)
            return HTTP(raw)
        report=video_search("research science",token,opener=fake)
        self.assertEqual(len(report["videos"]),1)
        self.assertEqual(report["videos"][0]["video_id"],"AbCdEf12345")
        self.assertNotIn(token,json.dumps(report))
        self.assertFalse(report["access_to_captions"])
        self.assertFalse(report["media_downloaded"])
        self.assertFalse(report["rights_to_republish"])

    def test_api_failure_redacts_request_uri(self):
        token="owner-private-test-key-123456"
        def fake(req,timeout):
            raise ValueError(req.full_url)
        with self.assertRaises(RuntimeError) as context:
            video_search("science lab",token,opener=fake)
        self.assertNotIn(token,str(context.exception))

    def test_credential_required(self):
        with self.assertRaises(ValueError):
            video_search("research","")
        with self.assertRaises(ValueError):
            video_search("research","owner-private-test-key-123456",channel="youtube.com/external")
        with self.assertRaises(ValueError):
            video_search("research","owner-private-test-key-123456",max_results=100)

if __name__=="__main__":
    unittest.main()
