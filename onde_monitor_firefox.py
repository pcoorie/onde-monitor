#!/usr/bin/env python3
"""
onde_monitor_firefox.py
Firefox-only version of onde_monitor.py.

Monitors operator.onde.app for "Auto Search" and sends SMS alerts via ClickSend.
Reads the page from your already-running, already-logged-in Firefox over
Marionette (Firefox's built-in remote control socket) — no Selenium, no
geckodriver, no pip installs.

Firefox must be started with Marionette enabled:

    /Applications/Firefox.app/Contents/MacOS/firefox -marionette

(Quit Firefox first; the flag only takes effect at launch.)
"""

import os
import socket
import time
import logging
import urllib.request
import json
import sys
from pathlib import Path

# ── .env loading (no third-party deps) ────────────────────────────────────────

def load_env_file(path: Path) -> None:
    """Populate os.environ from a simple KEY=VALUE .env file, if present."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())

load_env_file(Path(__file__).resolve().parent / ".env")

# ── Configuration ────────────────────────────────────────────────────────────

CLICKSEND_USERNAME = os.environ["CLICKSEND_USERNAME"]
CLICKSEND_API_KEY  = os.environ["CLICKSEND_API_KEY"]
SMS_FROM           = "PickMe"          # Registered ClickSend alpha tag
SMS_RECIPIENTS     = [
    p.strip() for p in os.environ["SMS_RECIPIENTS"].split(",") if p.strip()
]

TRIP_URL               = "https://operator.onde.app/"
TRIP_URL_MATCH         = "operator.onde.app"

MARIONETTE_HOST        = "127.0.0.1"
MARIONETTE_PORT        = 2828

CHECK_INTERVAL_SECONDS = 30

LOG_FILE = Path.home() / "Library" / "Logs" / "onde_monitor_firefox.log"

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("onde_monitor_firefox")


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


# ── Page check via Marionette ─────────────────────────────────────────────────
class Marionette:
    """Minimal Marionette (protocol v3) client over a local TCP socket.

    Packets are framed as `<byte-length>:<json>`. Commands are
    `[0, id, name, params]`; replies are `[1, id, error, result]`.
    """

    def __init__(self, host: str = MARIONETTE_HOST, port: int = MARIONETTE_PORT):
        self.sock = socket.create_connection((host, port), timeout=10)
        self.sock.settimeout(30)
        self._id = 0
        hello = self._read_packet()
        if hello.get("marionetteProtocol") != 3:
            raise RuntimeError(f"Unsupported Marionette handshake: {hello}")
        self.command("WebDriver:NewSession", {"strictFileInteractability": False})

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass

    def _recv_exact(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("Marionette connection closed")
            buf += chunk
        return buf

    def _read_packet(self):
        header = b""
        while not header.endswith(b":"):
            header += self._recv_exact(1)
        length = int(header[:-1])
        return json.loads(self._recv_exact(length).decode("utf-8"))

    def command(self, name: str, params: dict | None = None):
        self._id += 1
        body = json.dumps([0, self._id, name, params or {}]).encode("utf-8")
        self.sock.sendall(str(len(body)).encode() + b":" + body)
        while True:
            msg = self._read_packet()
            if isinstance(msg, list) and msg[0] == 1 and msg[1] == self._id:
                _, _, error, result = msg
                if error:
                    raise RuntimeError(f"{name}: {error.get('error')}: {error.get('message')}")
                return result


_client: Marionette | None = None


def get_page_text() -> str:
    """Return document.body.innerText of the operator.onde.app tab in Firefox."""
    global _client
    try:
        if _client is None:
            _client = Marionette()
        handles = _client.command("WebDriver:GetWindowHandles")
        for handle in handles:
            # focus=False switches the automation target without raising the tab
            _client.command("WebDriver:SwitchToWindow", {"handle": handle, "focus": False})
            url = _client.command("WebDriver:GetCurrentURL")["value"]
            if TRIP_URL_MATCH in url:
                result = _client.command("WebDriver:ExecuteScript", {
                    "script": "try { return document.body.innerText } catch(e) { return '' }",
                    "args": [],
                })
                return result.get("value") or ""
        log.warning(f"No Firefox tab found with {TRIP_URL_MATCH} in its URL")
        return ""
    except (OSError, ConnectionError) as e:
        log.warning(
            f"Marionette connection problem ({e}). Is Firefox running with "
            f"-marionette? Will retry."
        )
        if _client:
            _client.close()
        _client = None
        return ""
    except Exception as e:
        # Protocol-level error (e.g. tab closed mid-check): reconnect next time.
        log.warning(f"Marionette error: {e}")
        if _client:
            _client.close()
        _client = None
        return ""


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
STATE_FILE = Path.home() / ".onde_monitor_firefox_state.json"

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
    log.info("onde_monitor_firefox starting up…")
    log.info(f"Polling every {CHECK_INTERVAL_SECONDS}s  |  Alerts → {SMS_RECIPIENTS}")
    log.info(f"Watching: {TRIP_URL} (Firefox via Marionette {MARIONETTE_HOST}:{MARIONETTE_PORT})")

    state = load_state()

    while True:
        try:
            page_text = get_page_text()
            if not page_text:
                # Couldn't read the page — don't treat it as "no trips", or
                # alerted entries would be cleared and re-sent next time.
                time.sleep(CHECK_INTERVAL_SECONDS)
                continue

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
