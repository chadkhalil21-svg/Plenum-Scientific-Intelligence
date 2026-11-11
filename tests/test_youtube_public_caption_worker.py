"""No paid APIs: exact original founder event, six reviewed IDs, truthful caption facts."""
import unittest
from pathlib import Path
from plenum_ai import youtube_public_caption_worker as w

IDS=["VR35PxCFZIQ","LqVJORn7ogE","fCHe_fOqlYA","9Hwanevuhd8","MvJeDME7NN8","GMcLy4Gn7GU"]

def event(ids=IDS, *, title=w.TITLE, owner=w.OWNER):
    return {"action":"opened","repository":{"full_name":w.REPO},
     "issue":{"number":745,"user":{"login":owner},"title":title,
      "body":w.MARKER+"\nvideos: "+",".join(ids)}}

class FakeCaptions:
    def to_raw_data(self):
        return [{"start":float(i*10),"text":(
            "Gamma and Napkin AI are software; try Consensus and NotebookLM"
            if i==1 else "Public commentary about scientific research and data processing")}
             for i in range(10)]

class PublicCaptionTests(unittest.TestCase):
    def test_original_founder_video_request_validation(self):
        self.assertEqual(w.parse_owner_event(event()),IDS)
        for bad in (event(title="other"),event(owner="outsider"),
                    event(ids=["not-an-ID"]),event(ids=IDS+IDS),
                    event(ids=["VR35PxCFZIQ"]*2)):
            with self.subTest(bad=str(bad)[:55]):
                with self.assertRaises((ValueError,PermissionError)):
                    w.parse_owner_event(bad)
    def test_strict_six_video_public_references(self):
        data=w.load_catalog()
        self.assertEqual(set(data),set(IDS))
        self.assertEqual(len(data["MvJeDME7NN8"]["platforms"]),13)
        self.assertIn("Docling",[x["name"] for x in data["MvJeDME7NN8"]["platforms"]])
        self.assertFalse(data["fCHe_fOqlYA"]["coverage"]["full_visual_playback"])
    def test_real_caption_names_timestamps_without_transcript_copy(self):
        data=w.load_catalog()
        report=w.research(["VR35PxCFZIQ"],data,fetch=lambda id: FakeCaptions())
        self.assertEqual(report["captions_retrieved"],1)
        self.assertFalse(report["text_or_audio_saved"])
        names=[x["name"] for x in report["outcomes"][0]["platforms"] if x["found_in_caption"]]
        self.assertIn("Gamma",names)
        self.assertIn("Napkin AI",names)
        self.assertEqual(report["outcomes"][0]["caption_segments_count"],10)
        self.assertNotIn("Public commentary",str(report))
        self.assertFalse(report["outcomes"][0]["platform_list_complete_by_captions_alone"])
    def test_caption_network_block_not_called_success(self):
        data=w.load_catalog()
        def blocked(id):
            raise OSError("cloud-ip-blocked")
        report=w.research(["LqVJORn7ogE"],data,fetch=blocked)
        self.assertEqual(report["captions_retrieved"],0)
        self.assertEqual(report["outcomes"][0]["status"],"CAPTION_UNAVAILABLE")
        self.assertEqual(report["outcomes"][0]["failure_type"],"OSError")
        self.assertNotIn("cloud-ip-blocked",str(report))
    def test_no_unapproved_video_can_be_fetched(self):
        with self.assertRaises(ValueError):
            w.research(["dQw4w9WgXcQ"],w.load_catalog(),fetch=lambda id: FakeCaptions())

if __name__=="__main__":
    unittest.main()
