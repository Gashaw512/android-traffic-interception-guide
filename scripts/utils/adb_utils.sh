#!/bin/bash
# utils/adb_utils.sh
# Provides functions for Android ADB-related operations for burpDrop.

# Define the device certificate directory on Android
DEVICE_CERT_DIR="/system/etc/security/cacerts"

# Function to check if an Android device is connected and ready.
# Returns 0 on success, 1 on failure.
ensure_device_ready() {
    log_info "Checking for connected Android device..."
    local retries=5
    local count=0

    while [[ $count -lt $retries ]]; do
        local device_state=$(adb get-state 2>/dev/null || true)
        if [[ "$device_state" == "device" ]]; then
            log_success "ADB device detected and ready."
            return 0
        elif [[ "$device_state" == "offline" ]]; then
            log_warn "Device is offline. Please check connection. Retrying in 5 seconds..."
        else
            log_warn "No ADB device found or device state is '$device_state'. Please ensure your Android emulator/device is running and connected via ADB. Retrying in 5 seconds..."
        fi
        sleep 5
        count=$((count + 1))
    done

    log_error "Failed to detect a ready ADB device after multiple attempts."
    return 1
}

# Function to obtain root access and remount /system as read-write.
# Returns 0 on success, 1 on failure.
adb_root_remount() {
    log_info "Attempting to get root access via 'adb root'..."
    if ! adb root; then
        log_error "Failed to get root access. This device might not be rooted or 'adb root' is not supported."
        log_error "Please ensure your device is rooted and 'adb root' works manually, then try again."
        return 1
    fi
    log_success "Root access obtained."

    log_info "Attempting to remount /system partition as read-write..."
    if ! adb remount; then
        log_error "Failed to remount /system as read-write."
        log_error "You might need to disable verity or flash a custom recovery. Try 'adb disable-verity' and reboot, then try again."
        return 1
    fi
    log_success "/system partition remounted successfully (read-write)."
    return 0
}

# Function to backup an existing certificate on the device.
# Arguments:
#   $1 - The filename of the certificate on the device (e.g., '9a5ba575.0')
backup_remote_cert() {
    local cert_filename="$1"
    log_info "Checking for existing certificate '$DEVICE_CERT_DIR/$cert_filename' on device for backup..."

    # Check if the certificate file exists on the device
    if adb shell "ls $DEVICE_CERT_DIR/$cert_filename" >/dev/null 2>&1; then
        local timestamp=$(date +%Y%m%d_%H%M%S)
        local backup_file="$DEVICE_CERT_DIR/$cert_filename.bak.$timestamp"
        log_warn "Existing certificate found. Backing up to '$backup_file'..."
        if adb shell "cp $DEVICE_CERT_DIR/$cert_filename $backup_file"; then
            log_success "Backup created successfully."
        else
            log_error "Failed to create backup of existing certificate."
        fi
    else
        log_info "No existing certificate '$cert_filename' found on device. No backup needed."
    fi
}

# Function to push the new certificate to the device and set permissions.
# Arguments:
#   $1 - Local path to the hashed certificate file
#   $2 - Filename of the certificate on the device (e.g., '9a5ba575.0')
push_certificate_to_device() {
    local local_cert_path="$1"
    local device_cert_filename="$2"
    local device_target_path="$DEVICE_CERT_DIR/$device_cert_filename"

    log_info "Pushing certificate '$local_cert_path' to device at '$device_target_path'..."
    if ! adb push "$local_cert_path" "$device_target_path"; then
        log_error "Failed to push certificate to device."
        return 1
    fi
    log_success "Certificate pushed successfully."

    log_info "Setting permissions (chmod 644) for '$device_target_path'..."
    if ! adb shell "chmod 644 $device_target_path"; then
        log_error "Failed to set permissions for the certificate."
        return 1
    fi
    log_success "Permissions set to 644."
    return 0
}

# Function to reboot the device and wait for it to come back online.
reboot_and_wait() {
    log_info "Rebooting Android device..."
    if ! adb reboot; then
        log_error "Failed to initiate device reboot."
        return 1
    fi
    log_info "Device is rebooting. Waiting for it to come back online (this may take a minute or two)..."
    adb wait-for-device
    log_success "Device has rebooted and is back online."
    return 0
}
