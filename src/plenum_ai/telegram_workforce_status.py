"""Opt-in Telegram group status for existing PUBLIC founder tasks only.

No private task text, customer data, prompts, model output or tokens in logs.
Credentials are read from GitHub Action secrets, never stored in the repo.
"""
import argparse
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

KINDS = {"public_research", "public_program", "public_science", "public_creative"}
STATES = {
    "DRAFT_READY_FOR_FOUNDER", "BLOCKED_WORKER_FAILED",
    "BLOCKED_WORKER_UNAVAILABLE", "BLOCKED_VERIFICATION",
    "BLOCKED_NO_SOURCE_EVIDENCE", "BLOCKED_WORKER_OR_VERIFICATION",
}
REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence"


def build_notice(report: dict, run_id: str) -> str:
    if not isinstance(report, dict):
        raise ValueError("Missing status object")
    kind = report.get("kind")
    status = report.get("status")
    issue = report.get("issue_number")
    if kind not in KINDS or status not in STATES:
        raise ValueError("Only bounded, known public task results may be announced")
    if not isinstance(issue, int) or not 1 <= issue <= 99999999:
        raise ValueError("Invalid public Issue ID")
    if not re.fullmatch(r"[0-9]{1,20}", str(run_id)):
        raise ValueError("GitHub Action run ID required")
    label = kind.removeprefix("public_").capitalize()
    return (
        "👑 Plenum Workforce — " + label + "\n"
        "Result: " + status + "\n"
        "Founder review is required; output is not approved publication.\n"
        "Issue: https://github.com/" + REPO + "/issues/" + str(issue) + "\n"
        "Run: https://github.com/" + REPO + "/actions/runs/" + run_id
    )


def send_notice(message: str, *, bot_token: str, chat_id: str,
                opener=urlopen) -> bool:
    if not bot_token or not chat_id:
        return False
    if (not re.fullmatch(r"[0-9]{5,20}:[A-Za-z0-9_-]{25,}", bot_token)
            or not re.fullmatch(r"-?[0-9]{5,24}", chat_id)):
        raise ValueError("Bot credential or group destination is invalid")
    if len(message) > 800:
        raise ValueError("Unexpectedly long public notification")
    payload = json.dumps({
        "chat_id": chat_id, "text": message,
        "disable_web_page_preview": True,
    }).encode("utf-8")
    request = Request(
        "https://api.telegram.org/bot" + bot_token + "/sendMessage",
        data=payload, headers={"Content-Type": "application/json"},
        method="POST",
    )
    with opener(request, timeout=12) as response:
        data = json.loads(response.read(10001))
    if data.get("ok") is not True:
        raise RuntimeError("Telegram declined bounded public task status")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--status-file", required=True)
    args = parser.parse_args()
    token = os.getenv("PLENUM_TELEGRAM_BOT_TOKEN", "")
    chat = os.getenv("PLENUM_TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        print("TELEGRAM_STATUS NOT_CONFIGURED; no message attempted")
        return
    report = json.loads(Path(args.status_file).read_text(encoding="utf-8"))
    msg = build_notice(report, os.getenv("GITHUB_RUN_ID", ""))
    send_notice(msg, bot_token=token, chat_id=chat)
    print("TELEGRAM_STATUS SENT_PUBLIC_RESULT_ONLY")


if __name__ == "__main__":
    main()
