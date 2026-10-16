# Onde Monitor

A Python-based monitoring and automation tool for managing Onde systems.

## Overview

This project provides various tools and scripts to automate monitoring tasks, manage keychain operations, and interact with Firefox browsers to perform automated actions.

## Project Structure

- `onde_monitor.py` - Main monitor script
- `onde_monitor_firefox.py` - Firefox automation scripts  
- `onde_monitor_keychain.py` - Keychain related functions
- `run_onde_monitor_firefox.sh` - Shell script to run Firefox automation
- `setup_keychain.sh` - Shell script for keychain setup
- `run_onde_monitor.applescript` - macOS AppleScript for running monitor
- `run_onde_monitor_firefox.applescript` - macOS AppleScript for running Firefox monitor

## Features

- Automated monitoring capabilities
- Keychain management automation
- Firefox browser automation
- Cross-platform compatibility (macOS specifically designed)
- Configuration through environment variables

## Setup

1. Clone or download this repository
2. Make scripts executable:
   ```bash
   chmod +x run_onde_monitor_firefox.sh
   chmod +x setup_keychain.sh
   ```
3. Configure environment variables in `.env` file (refer to `.env.example`)

## Usage

### Running Monitor Scripts

- Use `run_onde_monitor_firefox.sh` to run Firefox automation scripts
- Or use the AppleScript files for macOS GUI integration

## Requirements

- Python 3.x
- macOS (for AppleScript functionality)
- Firefox browser
- Keychain access permissions

## License

MIT