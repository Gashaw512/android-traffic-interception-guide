#!/bin/bash
# utils/logger.sh
# Provides timestamped logging functions for burpDrop.

# Define the log directory (should be set in the main script)
: "${LOG_DIR:?LOG_DIR is not set. Please ensure LOG_DIR is defined before sourcing logger.sh}"

# Create the log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Define the log file name with a unique timestamp
# YYYYMMDD-HHMMSS format
LOG_FILE="$LOG_DIR/install-$(date +%Y%m%d-%H%M%S).log"

# Function to log messages to console and file
# Arguments:
#   $1 - The message to log
#   $2 - (Optional) The log level (e.g., INFO, SUCCESS, ERROR, WARN)
log() {
    local timestamp="[$(date +%H:%M:%S)]"
    local message="$1"
    local level="${2:-INFO}" # Default level is INFO if not provided

    # Print to console
    echo -e "$timestamp [$level] $message"

    # Append to log file
    echo "$timestamp [$level] $message" >> "$LOG_FILE"
}

# Convenience functions for different log levels
log_info() {
    log "$1" "INFO"
}

log_success() {
    log "✅ $1" "SUCCESS"
}

log_error() {
    log "❌ $1" "ERROR"
}

log_warn() {
    log "⚠️  $1" "WARNING"
}
