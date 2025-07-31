#!/bin/bash

# burpdrop.sh
# Launcher script for burpDrop.py on Linux and macOS.

# Exit immediately if a command exits with a non-zero status.
set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Path to the main Python script
PYTHON_SCRIPT="$SCRIPT_DIR/burpDrop.py"

# --- Check for Python ---
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not found in your PATH."
    echo "Please install Python 3 and ensure it's accessible."
    exit 1
fi

# --- Install Python Dependencies (Optional but Recommended) ---
# This part can be uncommented if you want the launcher to
# automatically install dependencies if they are missing.
# However, for a cleaner setup, it's often better to instruct
# the user to run 'pip install -r requirements.txt' manually.
#
# echo "Installing/updating Python dependencies..."
# python3 -m pip install -r "$SCRIPT_DIR/requirements.txt" || {
#     echo "❌ Failed to install Python dependencies. Please run 'pip install -r requirements.txt' manually."
#     exit 1
# }

# --- Execute the Python script ---
echo "🚀 Launching burpDrop..."
python3 "$PYTHON_SCRIPT" "$@"
