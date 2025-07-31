#!/bin/bash
# utils/dependencies.sh
# Checks for required system dependencies (adb, openssl) for burpDrop.

# Function to check if required command-line tools are available
check_dependencies() {
    log_info "Verifying required dependencies (adb, openssl)..."
    local missing_tools=()

    # Iterate through each required tool
    for tool in adb openssl; do
        # Check if the command exists in the system's PATH
        if ! command -v "$tool" >/dev/null 2>&1; then
            missing_tools+=("$tool")
        fi
    done

    # Report findings
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "The following required tools are NOT found: ${missing_tools[*]}."
        log_error "Please install them and ensure they are in your system's PATH."
        log_error "  - For ADB: Install Android SDK Platform-Tools (developer.android.com/studio/releases/platform-tools)"
        log_error "  - For OpenSSL: Install from your OS package manager (e.g., 'sudo apt install openssl' on Debian/Ubuntu, 'brew install openssl' on macOS)"
        exit 1 # Exit the script if dependencies are missing
    else
        log_success "All required dependencies (adb, openssl) found."
    fi
}
