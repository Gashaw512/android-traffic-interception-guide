#!/bin/bash

# test_utils.sh – Basic sanity checks for burpDrop shell utilities

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UTILS_DIR="$PROJECT_ROOT/scripts/utils"

source "$UTILS_DIR/logger.sh"
source "$UTILS_DIR/dependencies.sh"
source "$UTILS_DIR/adb_utils.sh"
source "$UTILS_DIR/cert_utils.sh"

echo "🔍 Running shell utility tests..."

# Test logger
log_info    "✅ logger.sh - Info log test"
log_success "✅ logger.sh - Success log test"
log_error   "✅ logger.sh - Error log test"
log_warn    "✅ logger.sh - Warning log test"

# Test dependencies
echo "🧪 Checking dependencies..."
check_dependencies && log_success "✅ dependencies.sh - All dependencies found"

# Test ADB (mocked)
echo "🧪 Checking ADB status..."
if ensure_device_ready; then
    log_success "✅ adb_utils.sh - Device is ready"
else
    log_warn "⚠️ adb_utils.sh - No device connected (expected if no emulator)"
fi

# Certificate conversion dry test
DER_TEST_FILE="$PROJECT_ROOT/assets/sample.der"
if [[ -f "$DER_TEST_FILE" ]]; then
    echo "🧪 Testing cert conversion..."
    converted=$(convert_cert "$DER_TEST_FILE") || log_error "❌ cert_utils.sh - Conversion failed"
    [[ -f "$converted" ]] && log_success "✅ cert_utils.sh - Conversion successful: $converted"
else
    log_warn "⚠️ Skipping cert conversion test – $DER_TEST_FILE not found"
fi

echo "🎉 All utility tests completed."
