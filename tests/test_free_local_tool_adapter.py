"""Focused, independent tests of new local-only free-tool adapter."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from plenum_ai.free_local_tool_adapter import probe, transcribe_local


class FreeLocalToolsTests(unittest.TestCase):
    def test_probe_never_claims_models_or_host(self):
        found=probe(find_binary=lambda command: "/bin/" + command if command=="ffmpeg" else None)
        self.assertTrue(found["binaries"]["ffmpeg"])
        self.assertFalse(found["binaries"]["Ollama"])
        self.assertFalse(found["binaries"]["whisper.cpp"])
        self.assertFalse(found["permanent_server_verified"])
        self.assertFalse(found["installed_by_plenum_tool"])

    def test_no_owner_approval_and_no_ci_private_media(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); audio=root/"sample.wav";model=root/"tiny.bin"
            audio.write_bytes(b"RIFF" + b"X"*100)
            model.write_bytes(b"model")
            with patch.dict(os.environ,{"PLENUM_OWNER_LOCAL_MEDIA":""},clear=False):
                with self.assertRaises(PermissionError):
                    transcribe_local(workspace=root,wav_file=audio,model_file=model,
                                     find_binary=lambda _: "/bin/whisper-cli")
            with patch.dict(os.environ,{"PLENUM_OWNER_LOCAL_MEDIA":"authorized",
                                        "GITHUB_ACTIONS":"true"},clear=False):
                with self.assertRaises(PermissionError):
                    transcribe_local(workspace=root,wav_file=audio,model_file=model,
                                     find_binary=lambda _: "/bin/whisper-cli")

    def test_only_local_whisper_can_create_transcript(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);audio=root/"owned.wav";model=root/"tiny.bin"
            audio.write_bytes(b"RIFF" + b"X"*100)
            model.write_bytes(b"model")
            calls=[]
            def fake(cmd, **kwargs):
                calls.append((cmd,kwargs))
                output_base=Path(cmd[cmd.index("-of")+1])
                output_base.with_suffix(".txt").write_text("A permitted local transcription\n")
                class Run: returncode=0
                return Run()
            with patch.dict(os.environ,{"PLENUM_OWNER_LOCAL_MEDIA":"authorized",
                                        "GITHUB_ACTIONS":"false"},clear=False):
                result=transcribe_local(workspace=root,wav_file=audio,model_file=model,
                              runner=fake,find_binary=lambda _: "/bin/whisper-cli")
            self.assertEqual(result["status"],"LOCAL_TRANSCRIPT_FILE_CREATED")
            self.assertTrue(Path(result["file"]).exists())
            self.assertEqual(len(calls),1)
            self.assertNotIn("http",str(calls))
            self.assertEqual(calls[0][0][0],"/bin/whisper-cli")
            self.assertFalse(result["paid_service_invoked"])

    def test_refuse_external_or_ambiguous_file(self):
        with TemporaryDirectory() as temp:
            root=Path(temp);out=root/"owned.wav";model=root/"tiny.bin"
            out.write_bytes(b"RIFF" + b"X"*10);model.write_bytes(b"model")
            sub=root/"sub";sub.mkdir()
            link=sub/"incoming.wav";link.symlink_to(out)
            with patch.dict(os.environ,{"PLENUM_OWNER_LOCAL_MEDIA":"authorized",
                                        "GITHUB_ACTIONS":"false"},clear=False):
                with self.assertRaises(ValueError):
                    transcribe_local(workspace=root,wav_file=link,model_file=model,
                                     find_binary=lambda _: "/bin/whisper-cli")
                with self.assertRaises(ValueError):
                    transcribe_local(workspace=root,wav_file=root/"none.mp3",model_file=model,
                                     find_binary=lambda _: "/bin/whisper-cli")


if __name__=="__main__":
    unittest.main()
