"""Check the *real network* Uvicorn WebSocket upgrade, not TestClient.

Only loopback traffic. The existing /owner/live handler must reject an
anonymous connection with 403 after a genuine WebSocket protocol handshake.
A missing optional Uvicorn transport cannot perform that handshake and fails.
No owner credentials, external website, private cookie, or Chromium are used.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

from websockets.exceptions import InvalidStatus
from websockets.sync.client import connect


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def verify():
    port = free_port()
    env = os.environ.copy()
    # Require the original IAP branch to reject anonymous traffic, regardless
    # of any CI environment that accidentally sets the Cloud Run service name.
    env["K_SERVICE"] = "plenum-computer-browser"
    env["COMPUTER_BROWSER_CI_ONLY"] = "true"
    command = [
        sys.executable, "-m", "uvicorn",
        "services.computer_browser.api:app",
        "--host", "127.0.0.1",
        "--port", str(port),
        "--ws", "auto",
        "--log-level", "error",
    ]
    process = subprocess.Popen(
        command, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Uvicorn app exited before local WebSocket check")
            try:
                with urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.2)
        else:
            raise RuntimeError("Uvicorn health endpoint unavailable")
        address = (
            f"ws://127.0.0.1:{port}/owner/live"
            "?site=https%3A%2F%2Fexample.com%2F"
        )
        try:
            with connect(address, open_timeout=4):
                raise AssertionError("Anonymous browser must not be accepted")
        except InvalidStatus as failure:
            # FastAPI's pre-accept ws.close(4403) correctly gives HTTP 403.
            status = failure.response.status_code
            if status != 403:
                raise AssertionError(
                    f"Actual WebSocket upgrade failed with unexpected HTTP {status}"
                ) from None
        print("PASS: Real Uvicorn WebSocket transport reached owner policy and denied anonymous handshake (403).")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


if __name__ == "__main__":
    verify()
