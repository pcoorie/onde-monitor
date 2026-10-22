#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import base64
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent / ".env"
with open(env_path, 'r') as f:
    for line in f:
        if line.strip() and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

# Extract configuration
CLICKSEND_USERNAME = os.environ["CLICKSEND_USERNAME"]
CLICKSEND_API_KEY = os.environ["CLICKSEND_API_KEY"]
SMS_RECIPIENTS = [p.strip() for p in os.environ["SMS_RECIPIENTS"].split(",") if p.strip()]
SMS_FROM = os.environ.get("SMS_FROM", "+1234567890")

print(f"Configuration loaded:")
print(f"  Username: {CLICKSEND_USERNAME}")
print(f"  API Key: {CLICKSEND_API_KEY[:5]}...")  
print(f"  Recipients: {SMS_RECIPIENTS}")
print(f"  From: {SMS_FROM}")

def send_sms(message: str, recipients: list | None = None) -> bool:
    """Send an SMS via ClickSend."""
    targets = recipients if recipients is not None else SMS_RECIPIENTS
    if not targets:
        print("No recipients - no SMS sent")
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
                print(f"SMS sent successfully to {targets}")
                return True
            else:
                print(f"ClickSend response: {body}")
                return False
    except Exception as e:
        print(f"SMS send failed: {e}")
        return False

# Test the function
print("\nTesting SMS sending...")
test_message = "Test message from standalone script"
result = send_sms(test_message)
print(f"Result: {result}")