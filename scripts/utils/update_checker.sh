#!/bin/bash
# utils/update_checker.sh
# Checks for the latest version of burpDrop on GitHub.

# GitHub repository details
REPO="gashawkidanu/burpDrop"
# Define the current local version of your script
LOCAL_VERSION="1.1.0"

# Function to check for updates
check_for_updates() {
    log_info "Checking for updates to burpDrop..."

    # Check if 'curl' is installed, as it's required for this check
    if ! command -v curl >/dev/null 2>&1; then
        log_warn "Curl is not installed. Skipping update check."
        return
    fi

    local latest_version=""
    # Fetch the latest release tag name from GitHub API
    # -s: Silent mode (don't show progress meter or error messages)
    # grep -Po: Perl-regexp, only print matching part
    # '"tag_name": "\K.*?(?=")': Regex to extract the tag_name value
    latest_version=$(curl -s "https://api.github.com/repos/$REPO/releases/latest" | grep -Po '"tag_name": "\K.*?(?=")' || true)

    # Compare versions
    if [[ -z "$latest_version" ]]; then
        log_warn "Could not retrieve latest version from GitHub. Network issue or API rate limit?"
    elif [[ "$latest_version" != "$LOCAL_VERSION" ]]; then
        log_warn "🚨 A new version is available: $latest_version (You are using $LOCAL_VERSION)"
        log_warn "📦 Please visit: https://github.com/$REPO/releases/latest to download the latest version."
    else
        log_success "You are running the latest version: $LOCAL_VERSION"
    fi
}
