#!/bin/bash
# utils/cert_utils.sh
# Handles certificate conversion and hashing logic for burpDrop.

# Define the temporary directory for certificate operations (should be set in main script)
: "${TEMP_CERT_DIR:?TEMP_CERT_DIR is not set. Please ensure TEMP_CERT_DIR is defined before sourcing cert_utils.sh}"

# Function to convert a DER certificate to PEM and generate its subject hash filename.
# Arguments:
#   $1 - Path to the input DER certificate file.
# Returns:
#   The full path to the newly created hashed certificate file (e.g., /tmp/burpcert.XXXXXX/9a5ba575.0)
#   Returns an empty string and logs error on failure.
generate_hashed_cert() {
    local input_cert="$1"
    local temp_pem_file="$TEMP_CERT_DIR/burp.pem" # Temporary PEM file
    local hashed_cert_name # Will store the hash (e.g., 9a5ba575)
    local final_hashed_path # Will store the final path (e.g., /tmp/.../9a5ba575.0)

    log_info "Converting DER certificate to PEM format..."
    # Convert DER to PEM using openssl
    if ! openssl x509 -inform der -in "$input_cert" -out "$temp_pem_file" 2>/dev/null; then
        log_error "Failed to convert DER certificate to PEM. Is '$input_cert' a valid DER file?"
        return 1
    fi
    log_success "Certificate converted to PEM: '$temp_pem_file'"

    log_info "Generating subject hash for the certificate..."
    # Generate the old-style subject hash required by Android
    # 'head -n 1' ensures we only get the hash, not other openssl output.
    hashed_cert_name=$(openssl x509 -inform pem -subject_hash_old -in "$temp_pem_file" 2>/dev/null | head -n 1)

    if [[ -z "$hashed_cert_name" ]]; then
        log_error "Failed to generate subject hash for the certificate."
        rm -f "$temp_pem_file" # Clean up temporary PEM file
        return 1
    fi
    log_success "Generated certificate hash: '$hashed_cert_name'"

    # Android system certificates are named with their subject hash followed by '.0'
    final_hashed_path="$TEMP_CERT_DIR/$hashed_cert_name.0"

    log_info "Renaming PEM file to its hashed name: '$final_hashed_path'"
    # Rename the temporary PEM file to its final hashed name
    if ! mv "$temp_pem_file" "$final_hashed_path"; then
        log_error "Failed to rename PEM file to '$final_hashed_path'."
        rm -f "$temp_pem_file" # Clean up temporary PEM file
        return 1
    fi
    log_success "Certificate prepared as '$final_hashed_path'."

    echo "$final_hashed_path" # Output the path to the main script
    return 0
}
