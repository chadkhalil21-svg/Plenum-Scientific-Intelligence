"""Independent frozen acceptance for malformed MusicBrainz work rows."""
import unittest
from plenum_ai.creative_sources import parse_musicbrainz

class CreativeMetadataAcceptance(unittest.TestCase):
    def test_malformed_neighbor_preserves_valid_work(self):
        ident = "b3b58a1b-7f6f-42f1-9c0d-6dd625ff1ace"
        valid = {"id":ident,"title":"Public catalog work","type":"Song"}
        for malformed in (None, 17, ["bad"], "bad"):
            with self.subTest(malformed=malformed):
                rows = parse_musicbrainz({"works":[malformed,valid]})
                self.assertEqual(len(rows),1)
                row = rows[0]
                self.assertEqual(row["title"],valid["title"])
                self.assertEqual(row["url"],"https://musicbrainz.org/work/"+ident)
                self.assertFalse(row["permission_to_reproduce_music"])
                self.assertFalse(row["recording_obtained"])
                self.assertFalse(row["music_notation_obtained"])

    def test_preserve_invalid_envelope_and_existing_bound(self):
        for malformed in (None,{},{"works":{}}):
            with self.assertRaises(ValueError):
                parse_musicbrainz(malformed)
        valid={"id":"b3b58a1b-7f6f-42f1-9c0d-6dd625ff1ace","title":"Catalog"}
        self.assertEqual(len(parse_musicbrainz({"works":[valid]*4})),3)
