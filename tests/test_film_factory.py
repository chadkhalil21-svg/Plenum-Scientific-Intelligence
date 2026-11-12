"""One bounded original MP4 acceptance and direct unsafe-input checks."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from plenum_ai.film_factory import render, validate, write_scene_caption_sidecar

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "terra_technical_demo.json"


class FilmFactoryTest(unittest.TestCase):
    def test_unsafe_media_and_unsupported_rights_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = json.loads(FIXTURE.read_text())
            data["scenes"][0].update({"type": "video", "path": "../secret.mp4", "license": "cc0"})
            with self.assertRaises(ValueError):
                validate(data, root)
            data["scenes"][0].update({"type": "video", "path": "clip.mp4", "license": "cc-by-nc"})
            (root / "clip.mp4").write_bytes(b"untrusted")
            with self.assertRaises(ValueError):
                validate(data, root)

    def test_original_narration_and_music_require_individual_rights(self):
        # Metadata-only validation; no new render or TTS call.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "voice.wav").write_bytes(b"author-owned-test-placeholder")
            (root / "score.wav").write_bytes(b"author-owned-test-placeholder")
            data = json.loads(FIXTURE.read_text())
            data["music"] = {
                "path": "score.wav", "creator": "Plenum composer",
                "license": "original", "origin": "self-composed", "rights_reviewed": True
            }
            data["narration"] = {
                "path": "voice.wav", "creator": "Plenum voice actor",
                "license": "original", "origin": "self-recorded", "rights_reviewed": True,
                "voice_usage_rights_reviewed": True
            }
            self.assertEqual(len(validate(data, root)), 4)
            data["narration"]["voice_usage_rights_reviewed"] = False
            with self.assertRaises(ValueError):
                validate(data, root)


    def test_accessible_caption_sidecar_uses_exact_scene_timing_without_voice_claims(self):
        data = json.loads(FIXTURE.read_text())
        for scene in data["scenes"]:
            scene["_frames"] = 60
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "film.srt"
            self.assertEqual(write_scene_caption_sidecar(data["scenes"], path), 4)
            content = path.read_text(encoding="utf-8")
            self.assertIn("00:00:00,000 --> 00:00:02,500", content)
            self.assertIn("00:00:07,500 --> 00:00:10,000", content)
            self.assertIn("An experimental concept, not proven results", content)
            self.assertEqual(content.count(" --> "), 4)
            self.assertNotIn("<script", content)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "System FFmpeg absent")
    def test_original_movie_has_real_audio_and_video(self):
        # One small integrated render, not every scene permutation.
        data = json.loads(FIXTURE.read_text())
        for scene in data["scenes"]:
            scene["seconds"] = 0.25
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "tiny.json"
            source.write_text(json.dumps(data), encoding="utf-8")
            report = render(source, root / "film")
            self.assertTrue(Path(report["film"]).is_file())
            self.assertEqual(report["status"], "TECHNICAL_RENDER_COMPLETE")
            self.assertFalse(report["natural_voice_approved"])
            self.assertFalse(report["public_distribution_approved"])
            self.assertTrue({"audio", "video"}.issubset({s["codec_type"] for s in report["ffprobe_streams"]}))
            self.assertGreater(Path(report["film"]).stat().st_size, 7000)
            self.assertEqual(report["subtitle_cues"], 4)
            self.assertEqual(report["caption_timing_scope"], "scene_boundaries_only_not_narration_word_aligned")
            self.assertTrue(Path(report["separate_subtitle_sidecar"]).is_file())
            self.assertEqual(Path(report["separate_subtitle_sidecar"]).read_text().count(" --> "), 4)


if __name__ == "__main__":
    unittest.main()
