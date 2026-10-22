# ONDE Monitor Project Memory

## Overview
This project monitors operator.onde.app for trips in "Auto Search" state and sends SMS alerts via ClickSend when new trips are found.

## Key Components

### Main Script (`onde_monitor.py`)
- Uses AppleScript to read page content from Chrome instead of Selenium
- Implements continuous monitoring loop with 30-second intervals
- Tracks alert state to prevent duplicate notifications
- Logs activities to ~/Library/Logs/onde_monitor.log

### Supporting Scripts
- `onde_monitor_keychain.py` - Likely handles secure credential storage using macOS Keychain
- `onde_monitor_firefox.py` - Alternative implementation for Firefox browser support

## Configuration Requirements
- `.env` file with:
  - `CLICKSEND_USERNAME`
  - `CLICKSEND_API_KEY`
  - `SMS_RECIPIENTS` (comma-separated list)

## Key Implementation Details
1. **Page Extraction**: Uses AppleScript to read text from running Chrome tab
2. **Trip Parsing**: Identifies trips in "Auto Search" state by analyzing page structure:
   - Looks for "Auto Search" lines that are at least 3 lines after address
   - Extracts "Preorder for ..." or "Scheduled for ..." timestamps
3. **Alert System**: Maintains state tracking to avoid duplicate alerts
4. **Error Handling**: Gracefully handles network errors and page parsing issues

## Known Patterns
- Trip addresses are found 3 lines before "Auto Search" entries
- Preorder times are found 1 line before "Auto Search" entries
- SMS format: "🚗 ONDE: Trip needs a driver!\n📍 Address\n⏰ Time"

## Monitoring Behavior
- Checks page every 30 seconds
- Sends alerts only when new trips are detected (not duplicates)
- Removes alerts from tracking when trips are no longer in "Auto Search"
- Maintains state in ~/.onde_monitor_state.json between runs

## Browser Requirements
- Chrome must be running with the operator.onde.app page open
- AppleScript access to Chrome needs to be enabled in System Preferences > Security & Privacy