"""Offline tests for pinned local-only model invocation: zero actual inference."""
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from plenum_ai import edge_runtime as edge


class LocalEdgeProofTests(unittest.TestCase):
    def test_plan_no_download_or_unearned_model_claim(self):
        p = edge.plan()
        self.assertIsNone(p["model_sha256"])
        self.assertFalse(p["model_downloads_authorized"])
        self.assertFalse(p["remote_inference_authorized"])
        self.assertFalse(p["inference_executed"])
        self.assertFalse(p["AGI_demonstrated"])
        self.assertFalse(p["network_isolation_independently_verified"])
        self.assertEqual(p["engine"], "ggml-org/llama.cpp")
        self.assertEqual(p["gpu_layers"], 0)

    def test_hash_contract_refuses_unreviewed_artifacts(self):
        for digest in ("", "0" * 63, "A" * 64, "x" * 64, 3, True):
            with self.subTest(digest=digest), self.assertRaises(ValueError):
                edge.plan(digest, "a" * 64)

    def test_explicit_execution_is_required_before_any_subprocess(self):
        with self.assertRaises(PermissionError):
            edge.execute(edge.plan(), runner=lambda *a, **k: self.fail("Runner invoked"))

    def _fixture(self, root):
        root = Path(root)
        (root / "models").mkdir()
        (root / "bin").mkdir()
        model = root / edge.MODEL
        engine = root / edge.ENGINE
        model.write_bytes(b"GGUF" + b"\x00" * 16)
        engine.write_bytes(b"#!/bin/sh\nexit 0\n")
        engine.chmod(0o700)
        model_hash = sha256(model.read_bytes()).hexdigest()
        engine_hash = sha256(engine.read_bytes()).hexdigest()
        return edge.plan(model_hash, engine_hash), model, engine

    def test_local_checksum_and_original_gguf_header_required(self):
        with tempfile.TemporaryDirectory() as d:
            p, model, engine = self._fixture(d)
            model.write_bytes(b"GHUF" + b"\x00" * 16)
            with self.assertRaises(ValueError):
                edge.execute(p, approved=True, assets_root=d,
                             runner=lambda *a, **k: self.fail("Runner invoked"))
            model.write_bytes(b"GGUF" + b"\x00" * 16)
            model.write_bytes(model.read_bytes() + b"tampered")
            with self.assertRaises(ValueError):
                edge.execute(p, approved=True, assets_root=d,
                             runner=lambda *a, **k: self.fail("Runner invoked"))
            model.write_bytes(b"GGUF" + b"\x00" * 16)
            engine.chmod(0o600)
            with self.assertRaises(ValueError):
                edge.execute(p, approved=True, assets_root=d,
                             runner=lambda *a, **k: self.fail("Runner invoked"))

    def test_symlink_rejected_including_parent_chain(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p, model, engine = self._fixture(root)
            model.unlink()
            (root / "hidden.gguf").write_bytes(b"GGUF" + b"data")
            model.symlink_to(root / "hidden.gguf")
            with self.assertRaises(ValueError):
                edge.execute(p, approved=True, assets_root=root,
                             runner=lambda *a, **k: self.fail("Runner invoked"))

    def test_modified_plan_rejected_even_if_files_exist(self):
        p = edge.plan("a" * 64, "b" * 64)
        p["max_new_tokens"] = 1000000
        with self.assertRaises(ValueError):
            edge.execute(p, approved=True, runner=lambda *a, **k: self.fail("Runner invoked"))

    def test_real_local_engine_contract_without_running_an_engine(self):
        with tempfile.TemporaryDirectory() as d:
            p, model, engine = self._fixture(d)
            calls = []
            ticks = iter((100.0, 102.125))
            def fake_runner(argv, **kw):
                calls.append((argv, kw))
                return subprocess.CompletedProcess(argv, 0, stdout="42", stderr="")
            with patch.dict(os.environ, {
                "OPENAI_API_KEY": "SECRET",
                "GITHUB_TOKEN": "SECRET",
                "ANTHROPIC_API_KEY": "SECRET",
                "HF_TOKEN": "SECRET",
            }):
                report = edge.execute(p, approved=True, assets_root=d,
                                      runner=fake_runner, clock=lambda: next(ticks))
            self.assertEqual(len(calls), 1)
            argv, kw = calls[0]
            self.assertEqual(argv[0], str(engine))
            self.assertEqual(argv[argv.index("-m") + 1], str(model))
            self.assertEqual(argv[argv.index("-ngl") + 1], "0")
            self.assertIn("--single-turn", argv)
            self.assertNotIn("-hf", argv)
            self.assertNotIn("shell", kw)
            self.assertFalse(kw["check"])
            self.assertEqual(kw["timeout"], edge.MAX_RUNTIME_SECONDS)
            for secret in ("OPENAI_API_KEY", "GITHUB_TOKEN", "ANTHROPIC_API_KEY", "HF_TOKEN"):
                self.assertNotIn(secret, kw["env"])
            self.assertEqual(report["elapsed_seconds"], 2.125)
            self.assertEqual(report["stdout_sha256"], sha256(b"42").hexdigest())
            self.assertEqual(report["stdout_characters"], 2)
            self.assertTrue(report["inference_executed"])
            self.assertFalse(report["independent_accuracy_verified"])
            self.assertIsNone(report["original_independent_correctness_score"])
            self.assertFalse(report["network_isolation_independently_verified"])
            self.assertFalse(report["AGI_demonstrated"])

    def test_nonzero_exit_is_not_success(self):
        with tempfile.TemporaryDirectory() as d:
            p, _, _ = self._fixture(d)
            result = edge.execute(
                p, approved=True, assets_root=d,
                runner=lambda argv, **kw: subprocess.CompletedProcess(
                    argv, 7, stdout="", stderr="Model mismatch"),
                clock=iter((3.0, 4.0)).__next__,
            )
            self.assertEqual(result["process_exit_code"], 7)
            self.assertFalse(result["inference_executed"])
            self.assertFalse(result["AGI_demonstrated"])


if __name__ == "__main__":
    unittest.main()
