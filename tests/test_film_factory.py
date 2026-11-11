"""One bounded original MP4 acceptance and direct unsafe-input checks."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from plenum_ai.film_factory import render, validate

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


if __name__ == "__main__":
    unittest.main()
