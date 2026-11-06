"""Original-only music-theory analysis tests."""
import importlib.util
import unittest
from plenum_ai.creative_studio import musicxml_study
from plenum_ai.music_analysis import analyze_original_music

class MusicAnalysisTests(unittest.TestCase):
    def test_source_is_original_deterministic_musicxml(self):
        score=musicxml_study("procedural light and sound",123)
        self.assertEqual(score,musicxml_study("procedural light and sound",123))
        self.assertEqual(score.count("<note>"),32)
        self.assertNotIn("<audio",score)

    @unittest.skipUnless(importlib.util.find_spec("music21"),"music21 is an optional isolated dependency")
    def test_real_music21_analyzer(self):
        r=analyze_original_music("procedural light and sound",123)
        self.assertEqual(r["note_count"],32)
        self.assertEqual(r["measures"],8)
        self.assertEqual(r["total_quarter_notes"],32)
        self.assertGreater(r["distinct_pitch_classes"],2)
        self.assertTrue(r["result_is_independent_music_analysis"])
        self.assertFalse(r["audio_generated_or_played"])
        self.assertFalse(r["copyrighted_source_score_imported"])
        self.assertFalse(r["artistic_quality_or_originality_verified"])

if __name__=="__main__":
    unittest.main()
