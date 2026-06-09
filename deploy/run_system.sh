#!/bin/bash
# =========================================================
# NTA REGISTRATION PORTAL - LINUX / MAC LAUNCHER
# This script delegates ALL logic to run_system.py
# =========================================================

# Go to the directory where this script lives (cross-platform)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python is available
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 is not installed or not in PATH."
    echo "Please install Python 3.10+: sudo apt install python3"
    exit 1
fi

# Launch the universal Python script
python3 run_system.py
