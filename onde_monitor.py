#!/usr/bin/env python3
"""
onde_monitor.py
Monitors operator.onde.app for "Auto Search" and sends SMS alerts via ClickSend.
Uses AppleScript to read the page from your already-running Chrome — no Selenium needed.
"""

import sys
import urllib.request
import json
import subprocess
import os
import logging
import time
from pathlib import Path
def load_env_file(path: Path) -> None:
    """Populate os.environ from a simple KEY=VALUE .env file, if present."""

    if not path.exists():
        return

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
load_env_file(Path(__file__).resolve().parent / ".env")

# ── Configuration ────────────────────────────────────────────────────────────

try:
    CLICKSEND_USERNAME = os.environ["CLICKSEND_USERNAME"]
    CLICKSEND_API_KEY  = os.environ["CLICKSEND_API_KEY"]
    SMS_RECIPIENTS     = [
        p.strip() for p in os.environ["SMS_RECIPIENTS"].split(",") if p.strip()
    ]
    SMS_FROM           = os.environ.get("SMS_FROM", "+1234567890")  # Default fallback number
except KeyError as e:
    print(f"Missing required environment variable: {e}")
    sys.exit(1)

TRIP_URL               = "https://operator.onde.app/"

CHECK_INTERVAL_SECONDS = 30

LOG_FILE = Path.home() / "Library" / "Logs" / "onde_monitor.log"

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("onde_monitor")


# ── SMS via ClickSend ─────────────────────────────────────────────────────────
def send_sms(message: str, recipients: list | None = None) -> bool:
    """Send an SMS via ClickSend.

    recipients: list of E.164 phone strings. Defaults to SMS_RECIPIENTS when None.
    Returns True on success.
    """
    import base64
    targets = recipients if recipients is not None else SMS_RECIPIENTS
    if not targets:
        log.warning("send_sms called with empty recipients list — no SMS sent")
        return False
    credentials = base64.b64encode(
        f"{CLICKSEND_USERNAME}:{CLICKSEND_API_KEY}".encode()
    ).decode()

    payload = json.dumps({
        "messages": [
            {"to": phone, "body": message, "from": SMS_FROM}
            for phone in targets
        ]
    }).encode()

    req = urllib.request.Request(
        "https://rest.clicksend.com/v3/sms/send",
        data=payload,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode())
            status = body.get("response_code", "")
            if status == "SUCCESS":
                log.info(f"SMS sent to {targets} ✓")
                return True
            else:
                log.warning(f"ClickSend response: {body}")
                return False
    except Exception as e:
        log.error(f"SMS send failed: {e}")
        return False


# ── Page check via AppleScript ────────────────────────────────────────────────
def get_page_text() -> str:
    """Read the trip page text from the running Chrome tab via AppleScript."""
    script = """
tell application "Google Chrome"
    set foundText to ""
    repeat with w in windows
        repeat with t in tabs of w
            if URL of t contains "operator.onde.app" then
                set foundText to execute t javascript "try { document.body.innerText } catch(e) { '' }"
                exit repeat
            end if
        end repeat
        if foundText is not "" then exit repeat
    end repeat
    return foundText
end tell
"""
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        log.warning(f"AppleScript error: {result.stderr.strip()}")
        return ""
    return result.stdout


def get_searching_trips(page_text: str) -> dict:
    """
    Parse the page text and return a dict of {address: preorder_time} for trips
    currently in Auto Search state.

    In the order list the structure is always:
        <address>       (line i-3)
        <customer name> (line i-2)
        Preorder for …  (line i-1)
        Auto Search …   (line i)
    """
    lines = [l.strip() for l in page_text.splitlines() if l.strip()]
    searching = {}
    for i, line in enumerate(lines):
        if line.startswith("Auto Search") and i >= 3:
            prev = lines[i - 1]
            if prev.startswith("Preorder for") or prev.startswith("Scheduled for"):
                address = lines[i - 3]
                searching[address] = prev  # e.g. "Preorder for 14:15"
    return searching


# ── State tracking ────────────────────────────────────────────────────────────
STATE_FILE = Path.home() / ".onde_monitor_state.json"

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
            return {"alerted": state.get("alerted", {})}
        except Exception:
            pass
    return {"alerted": {}}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    log.info("onde_monitor starting up…")
    log.info(f"Polling every {CHECK_INTERVAL_SECONDS}s  |  Alerts → {SMS_RECIPIENTS}")
    log.info(f"Watching: {TRIP_URL}")

    state = load_state()

    while True:
        try:
            page_text = get_page_text()
            searching = get_searching_trips(page_text)
            alerted   = state.get("alerted", {})

            log.info(f"Searching trips: {searching or 'none'}")

            # ── Auto Search alerts ────────────────────────────────────────────
            for address, preorder_time in searching.items():
                if address not in alerted:
                    msg = (
                        f"🚗 ONDE: Trip needs a driver!\n"
                        f"📍 {address}\n"
                        f"⏰ {preorder_time}"
                    )
                    send_sms(msg)
                    alerted[address] = 1

            for address in list(alerted.keys()):
                if address not in searching:
                    del alerted[address]

            state["alerted"] = alerted
            save_state(state)

        except Exception as e:
            log.error(f"Check failed: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Stopped by user")
