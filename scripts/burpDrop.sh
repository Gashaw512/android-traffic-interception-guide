#!/bin/bash

# burpDrop.sh
# Author: Gashaw Kidanu
# Version: 1.1.0
# Description: Full automation for converting, backing up, pushing, and installing Burp CA cert on Android emulator.

set -euo pipefail

# ============ CONFIG ============ #
LOG_DIR="logs"
SCRIPT_DIR=$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)
DEVICE_CERT_DIR="/system/etc/security/cacerts"
ADB_COMMAND=$(command -v adb)
OPENSSL_COMMAND=$(command -v openssl)

# ============ LOGGING ============ #
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/install-$(date +%Y%m%d-%H%M%S).log"

log() {
    echo -e "[$(date +%T)] $1" | tee -a "$LOG_FILE"
}

# ============ CLEANUP TEMPORARY FILES ============ #
TEMP_DIR=""
cleanup() {
    if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
        log "🧹 Cleaning up temporary directory: $TEMP_DIR"
        rm -rf "$TEMP_DIR"
    fi
}
trap cleanup EXIT # Ensure cleanup runs on exit

# ============ CHECK DEPENDENCIES ============ #
check_dependencies() {
    for tool in adb openssl; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            log "❌ Error: '$tool' not found. Please install it and ensure it's in your PATH."
            exit 1
        fi
    done
}

# ============ DEVICE STATUS ============ #
check_device_ready() {
    log "🔍 Checking ADB device connection..."
    local online=$(adb get-state 2>/dev/null || true)
    if [[ "$online" != "device" ]]; then
        log "❌ No Android device found. Ensure Genymotion is running and 'adb devices' shows the device."
        exit 1
    fi

    log "✅ Device detected."
}

# ============ BACKUP IF EXISTS ============ #
backup_remote_cert() {
    local cert_filename="$1"
    if adb shell ls "$DEVICE_CERT_DIR/$cert_filename" >/dev/null 2>&1; then
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_FILE="$DEVICE_CERT_DIR/$cert_filename.backup.$TIMESTAMP"
        log "📦 Backing up existing cert '$cert_filename' to '$BACKUP_FILE' on device."
        if ! adb shell cp "$DEVICE_CERT_DIR/$cert_filename" "$BACKUP_FILE"; then
            log "⚠️ Warning: Failed to backup existing certificate. Continuing without backup."
        fi
    fi
}

# ============ MAIN FUNCTION ============ #
install_certificate() {
    local INPUT_CERT="$1"

    if [[ ! -f "$INPUT_CERT" ]]; then
        log "❌ Error: Certificate file not found: $INPUT_CERT"
        exit 1
    fi

    # Create a temporary directory for processing
    TEMP_DIR=$(mktemp -d -t burpcert.XXXXXXXXXX)
    log "Created temporary directory: $TEMP_DIR"

    local TEMP_PEM="$TEMP_DIR/burp.pem"
    local FINAL_CERT_BASENAME="" # Will hold the hash.0 filename

    log "🔧 Converting DER to PEM..."
    if ! openssl x509 -inform der -in "$INPUT_CERT" -out "$TEMP_PEM"; then
        log "❌ Error: Failed to convert DER to PEM. Check if '$INPUT_CERT' is a valid DER certificate."
        exit 1
    fi

    log "🔍 Calculating subject hash..."
    local HASH=$(openssl x509 -inform pem -subject_hash_old -in "$TEMP_PEM" | head -n 1)
    FINAL_CERT_BASENAME="$HASH.0"
    local FINAL_CERT_PATH="$TEMP_DIR/$FINAL_CERT_BASENAME"

    log "📁 Renaming PEM to $FINAL_CERT_BASENAME..."
    if ! mv "$TEMP_PEM" "$FINAL_CERT_PATH"; then
        log "❌ Error: Failed to rename temporary PEM file."
        exit 1
    fi

    log "🚀 Preparing to push certificate to device..."
    check_device_ready

    log "Attempting to get root access on device..."
    if ! adb root; then
        log "❌ Error: Failed to get root access on the device. Ensure your emulator is rooted or Genymotion supports 'adb root'."
        log "Please manually run 'adb root' and ensure it succeeds before trying again, or try a different emulator image."
        exit 1
    fi
    log "Root access obtained."

    log "Attempting to remount /system partition as writable..."
    if ! adb remount; then
        log "❌ Error: Failed to remount /system partition as writable. This is critical for pushing the certificate."
        log "Ensure your emulator image supports 'adb remount'. You might need to disable verity (`adb disable-verity` then `adb reboot`) first."
        exit 1
    fi
    log "/system partition remounted as writable."

    backup_remote_cert "$FINAL_CERT_BASENAME"

    log "📤 Pushing '$FINAL_CERT_BASENAME' to '$DEVICE_CERT_DIR/' on device..."
    if ! adb push "$FINAL_CERT_PATH" "$DEVICE_CERT_DIR/"; then
        log "❌ Error: Failed to push certificate to device. Check device storage and permissions."
        exit 1
    fi

    log "⚙️ Setting permissions for '$FINAL_CERT_BASENAME'..."
    if ! adb shell chmod 644 "$DEVICE_CERT_DIR/$FINAL_CERT_BASENAME"; then
        log "⚠️ Warning: Failed to set permissions for the certificate. This might cause issues."
    fi

    log "🔁 Rebooting device to apply changes..."
    adb reboot

    log "Waiting for device to come back online..."
    adb wait-for-device
    sleep 5 # Give device a moment for services to start
    log "Device is online."

    log "✅ Certificate installation complete. Cert pushed as $FINAL_CERT_BASENAME. Please verify on device."
}

# ============ MENU UI ============ #
menu() {
    echo "\n📜 ADB Certificate Installer"
    echo "--------------------------------"
    select opt in "Install Certificate" "View Logs" "Exit"; do
        case $opt in
            "Install Certificate")
                log "💡 Export your Burp Suite CA certificate in DER format (e.g., cert.der) from Burp Proxy -> Options -> 'Import / export CA certificate' button."
                read -rp "📂 Enter path to cert.der: " cert_file
                install_certificate "$cert_file"
                break
                ;;
            "View Logs")
                if [[ -d "$LOG_DIR" && $(ls -1 "$LOG_DIR" | wc -l) -gt 0 ]]; then
                    log "Recent logs:"
                    ls -1 "$LOG_DIR" | tail -n 5
                    read -rp "🔍 Enter log filename to view (e.g., install-20231027-123456.log): " logname
                    if [[ -f "$LOG_DIR/$logname" ]]; then
                        less "$LOG_DIR/$logname"
                    else
                        log "❌ Log file not found: $LOG_DIR/$logname"
                    fi
                else
                    log "No logs found yet."
                fi
                ;;
            "Exit")
                echo "👋 Exiting."
                exit 0
                ;;
            *)
                echo "❌ Invalid option. Please choose again."
                ;;
        esac
        echo # Newline for better readability after each menu action
    done
}

# ============ ENTRYPOINT ============ #
check_dependencies
menu