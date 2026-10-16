# Setting up ClickSend Credentials in macOS Keychain

To securely store your ClickSend credentials in macOS Keychain, follow these steps:

## Add ClickSend Username and API Key to Keychain

### Step 1: Add the username (optional - if you want separate entries)
```bash
security add-generic-password -s "ClickSend" -a "your-clicksend-email@example.com" -p "your-clicksend-email@example.com" -T /usr/bin/security
```

### Step 2: Add the API key (this is the critical one)
```bash
security add-generic-password -s "ClickSend" -a "your-clicksend-email@example.com-api-key" -p "YOUR_CLICKSEND_API_KEY" -T /usr/bin/security
```

> Replace `YOUR_CLICKSEND_API_KEY` with your actual ClickSend API key from the .env file.

## Verify Credentials Were Added
```bash
security find-generic-password -s "ClickSend" -a "your-clicksend-email@example.com-api-key" -w
```

## Update Your Script to Use Keychain
1. Rename the original script `onde_monitor.py` to `onde_monitor_backup.py`
2. Copy or move your new keychain version `onde_monitor_keychain.py` as `onde_monitor.py`
3. Make the new script executable: `chmod +x onde_monitor.py`

## How the Script Works
The updated script will:
1. First try to retrieve credentials from macOS Keychain
2. Fall back to environment variables if keychain access fails
3. The credential service name used is "ClickSend"
4. The account names are:
   - `your-clicksend-email@example.com` (for username)
   - `your-clicksend-email@example.com-api-key` (for API key)

## Testing
Run the script to verify credentials can be retrieved properly:
```bash
python3 onde_monitor.py
```

The script should now retrieve credentials from Keychain rather than storing them in plaintext.