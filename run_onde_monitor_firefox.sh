#!/bin/bash
# Start Firefox with Marionette enabled (if needed), then run the Firefox monitor.
cd "$(dirname "$0")" || exit 1

ONDE_COMPANY_ID=$(grep '^ONDE_COMPANY_ID=' .env 2>/dev/null | cut -d'=' -f2-)
[ -n "$ONDE_COMPANY_ID" ] || { echo "ONDE_COMPANY_ID missing from .env"; exit 1; }
START_URL="https://operator.onde.app/view/${ONDE_COMPANY_ID}"

port_open() { nc -z 127.0.0.1 2828 >/dev/null 2>&1; }

if port_open; then
    echo "Firefox Marionette already available."
else
    if pgrep -x firefox >/dev/null; then
        echo "Firefox is running without Marionette; it must be restarted."
        read -r -p "Quit Firefox and relaunch it with -marionette? [y/N] " ans
        [[ "$ans" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
        osascript -e 'tell application "Firefox" to quit'
        for _ in $(seq 1 30); do pgrep -x firefox >/dev/null || break; sleep 1; done
        if pgrep -x firefox >/dev/null; then echo "Firefox didn't quit."; exit 1; fi
    fi
    echo "Launching Firefox with -marionette…"
    open -a Firefox --args -marionette "$START_URL"
    for _ in $(seq 1 30); do port_open && break; sleep 1; done
    port_open || { echo "Marionette didn't come up on port 2828."; exit 1; }
fi

echo "Make sure operator.onde.app is logged in in Firefox."
exec python3 onde_monitor_firefox.py
