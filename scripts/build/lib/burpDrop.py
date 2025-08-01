#!/usr/bin/env python3
import os
import subprocess
import platform
import datetime
import shutil
import sys
import atexit
import json
import re
import argparse
import time
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLOR_ENABLED = True
except ImportError:
    COLOR_ENABLED = False

# --- Constants ---
VERSION = "1.3.0"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
TEMP_CERT_DIR = os.path.join(SCRIPT_DIR, "temp_cert")
DEVICE_CERT_DIR = "/system/etc/security/cacerts"
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
HELP_TEXT = """
BurpDrop - Android Burp Certificate Installer

Commands:
  install   Install Burp certificate on Android device
  logs      View installation logs
  help      Show this help message

Options:
  --version  Show version information
  --help     Show help

Example:
  burpdrop install
"""

# --- Logger Class ---
class Logger:
    def __init__(self):
        self.log_file = os.path.join(LOG_DIR, f"burpdrop_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        os.makedirs(LOG_DIR, exist_ok=True)
        
    def log(self, message, level="INFO", color=None):
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
        log_entry = f"{timestamp} [{level}] {message}"
        
        # Print to console with color if available
        if COLOR_ENABLED and color:
            print(f"{color}{log_entry}{Style.RESET_ALL}")
        else:
            print(log_entry)
        
        # Write to log file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{log_entry}\n")
    
    def info(self, message):
        self.log(message, "INFO", Fore.CYAN if COLOR_ENABLED else None)
    
    def success(self, message):
        self.log(f"✓ {message}", "SUCCESS", Fore.GREEN if COLOR_ENABLED else None)
    
    def error(self, message):
        self.log(f"✗ {message}", "ERROR", Fore.RED if COLOR_ENABLED else None)
    
    def warn(self, message):
        self.log(f"⚠ {message}", "WARNING", Fore.YELLOW if COLOR_ENABLED else None)
    
    def progress(self, message, current, total):
        percent = int((current / total) * 100)
        progress_bar = f"[{'#' * int(percent/5)}{' ' * (20 - int(percent/5))}] {percent}%"
        self.info(f"{message} {progress_bar}")

# Initialize logger
logger = Logger()

# --- Cleanup Function ---
def cleanup():
    """Clean up temporary files"""
    if os.path.exists(TEMP_CERT_DIR):
        try:
            shutil.rmtree(TEMP_CERT_DIR)
            logger.info("Cleaned temporary files")
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")

# Register cleanup
atexit.register(cleanup)

# --- Configuration ---
def load_config():
    """Load configuration from JSON file"""
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info("Configuration loaded")
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
    else:
        logger.info("No config file found, using default settings")
    return config

def get_tool_path(tool_name, config):
    """Get path to tool with fallback to system PATH"""
    # Try config first
    config_path = config.get(f"{tool_name}_path")
    if config_path and os.path.exists(config_path):
        return config_path
    
    # Then try system PATH
    path_path = shutil.which(tool_name)
    if path_path:
        return path_path
    
    # Not found
    logger.error(f"{tool_name} not found. Please update config.json")
    return None

# --- Certificate Handling ---
def get_cert_file():
    """Prompt user for certificate file path"""
    logger.info("\nPlease provide the path to your Burp Suite .der certificate")
    logger.info("You can drag and drop the file into this window")
    logger.info("(Type 'help' for assistance or 'exit' to cancel)")
    
    while True:
        path = input("Certificate path: ").strip()
        
        if path.lower() == 'help':
            logger.info("Help: Export Burp certificate from Proxy > Proxy Settings /Options > Import/Export CA Certificate")
            logger.info("      Save as DER format and provide the path here")
            continue
            
        if path.lower() == 'exit':
            return None
            
        # Clean up user input
        path = re.sub(r'^["\']|["\']$', '', path)
        path = path.replace("\\ ", " ")
        
        if not path:
            continue
            
        if not os.path.exists(path):
            logger.error("File not found. Please try again.")
            continue
            
        if not path.lower().endswith('.der'):
            logger.warn("File doesn't have .der extension. Are you sure this is a Burp certificate?")
            confirm = input("Continue anyway? (y/n): ").strip().lower()
            if confirm != 'y':
                continue
                
        return os.path.abspath(path)

def convert_cert(cert_path, openssl_path):
    """Convert DER certificate to Android format"""
    try:
        # Ensure temp directory exists
        os.makedirs(TEMP_CERT_DIR, exist_ok=True)
        
        # Step 1: Convert DER to PEM
        logger.info("Converting certificate format...")
        pem_file = os.path.join(TEMP_CERT_DIR, "burp.pem")
        
        # Create parent directory if needed
        os.makedirs(os.path.dirname(pem_file), exist_ok=True)
        
        subprocess.run(
            [openssl_path, "x509", "-inform", "der", "-in", cert_path, "-out", pem_file],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.progress("Conversion progress", 1, 3)
        
        # Step 2: Get certificate hash
        result = subprocess.run(
            [openssl_path, "x509", "-inform", "pem", "-subject_hash_old", "-in", pem_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        cert_hash = result.stdout.splitlines()[0].strip()
        logger.progress("Processing certificate", 2, 3)
        
        # Step 3: Rename to Android format
        hash_file = os.path.join(TEMP_CERT_DIR, f"{cert_hash}.0")
        os.rename(pem_file, hash_file)
        logger.progress("Finalizing conversion", 3, 3)
        logger.success(f"Certificate prepared: {cert_hash}.0")
        
        return hash_file, cert_hash
        
    except subprocess.CalledProcessError as e:
        # Provide more detailed error message
        error_msg = e.stderr.decode().strip() if isinstance(e.stderr, bytes) else e.stderr.strip()
        logger.error(f"OpenSSL command failed: {error_msg}")
        
        # Suggest common solutions
        if "No such file or directory" in error_msg:
            logger.info("Possible solutions:")
            logger.info("1. Ensure the certificate path is correct")
            logger.info("2. Check directory permissions")
            logger.info("3. Verify OpenSSL has write access to temp_cert directory")
            
        return None, None
    except Exception as e:
        logger.error(f"Certificate processing error: {str(e)}")
        logger.info("Please check your certificate file and try again")
        return None, None

# --- ADB Operations ---
def run_adb_command(adb_path, command):
    """Execute an ADB command with error handling"""
    try:
        result = subprocess.run(
            [adb_path] + command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False  # Changed to False to capture specific remount errors
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except FileNotFoundError:
        logger.error("ADB executable not found. Check your config.json")
        return None, None, 1

def check_device_connection(adb_path):
    """Check if device is connected and ready"""
    logger.info("Checking device connection...")
    state, _, _ = run_adb_command(adb_path, ["get-state"])
    if state == "device":
        logger.success("Device connected and ready")
        return True
    logger.error("No device found or not ready")
    return False

def install_certificate(adb_path, cert_file, cert_hash):
    """Complete certificate installation workflow"""
    steps = 5
    current_step = 1
    
    # Get root access
    logger.info("Getting root access...")
    run_adb_command(adb_path, ["root"])
    logger.progress("Installation progress", current_step, steps)
    current_step += 1
    time.sleep(1) # Give device time to respond
    
    # Remount filesystem
    logger.info("Remounting filesystem...")
    stdout, stderr, returncode = run_adb_command(adb_path, ["remount"])
    if returncode != 0 or "remount succeeded" not in stdout.lower():
        logger.error("Failed to remount filesystem.")
        logger.error("Error: " + stderr)
        logger.info("This can happen if the device is not rooted or is protected by dm-verity.")
        logger.info("Try running 'adb disable-verity && adb reboot' manually before using burpdrop.")
        return False
    
    logger.success("Filesystem remounted as read-write")
    logger.progress("Installation progress", current_step, steps)
    current_step += 1
    
    # Push certificate
    logger.info("Pushing certificate to device...")
    remote_path = f"{DEVICE_CERT_DIR}/{cert_hash}.0"
    stdout, stderr, returncode = run_adb_command(adb_path, ["push", cert_file, remote_path])
    if returncode != 0:
        logger.error("Failed to push certificate.")
        logger.error("Error: " + stderr)
        return False
    logger.progress("Installation progress", current_step, steps)
    current_step += 1
    
    # Set permissions
    logger.info("Setting permissions...")
    stdout, stderr, returncode = run_adb_command(adb_path, ["shell", f"chmod 644 {remote_path}"])
    if returncode != 0:
        logger.error("Failed to set permissions.")
        logger.error("Error: " + stderr)
        return False
    logger.progress("Installation progress", current_step, steps)
    current_step += 1
    
    # Reboot device
    logger.info("Rebooting device...")
    run_adb_command(adb_path, ["reboot"])
    logger.info("Device rebooting. Please wait...")
    
    # Wait for device to reconnect
    run_adb_command(adb_path, ["wait-for-device"])
    logger.success("Device reconnected after reboot")
    logger.progress("Installation progress", current_step, steps)
    
    return True

# --- Log Viewer ---
def view_logs():
    """Display recent log files"""
    if not os.path.exists(LOG_DIR) or not os.listdir(LOG_DIR):
        logger.info("No log files available")
        return
    
    logs = [f for f in os.listdir(LOG_DIR) if f.startswith('burpdrop_')]
    logs.sort(reverse=True)
    
    print("\nRecent Log Files:")
    for i, log in enumerate(logs[:5], 1):
        print(f"{i}. {log}")
    
    try:
        selection = input("\nEnter log number to view (or Enter to go back): ").strip()
        if not selection:
            return
            
        index = int(selection) - 1
        if 0 <= index < len(logs):
            log_file = os.path.join(LOG_DIR, logs[index])
            with open(log_file, 'r', encoding='utf-8') as f:
                print("\n" + "="*60)
                print(f" Log File: {log_file} ".center(60))
                print("="*60)
                print(f.read())
                print("="*60)
                print("End of log".center(60))
                print("="*60)
        else:
            logger.error("Invalid selection")
    except (ValueError, IndexError):
        logger.error("Please enter a valid number")
    except Exception as e:
        logger.error(f"Error viewing log: {str(e)}")

# --- Main Workflow ---
def install_certificate_flow(config):
    """Complete certificate installation workflow"""
    # Load tool paths
    adb_path = get_tool_path("adb", config)
    openssl_path = get_tool_path("openssl", config)
    
    if not adb_path or not openssl_path:
        logger.error("Required tools not found. Check config.json")
        return
    
    # Get certificate
    cert_path = get_cert_file()
    if not cert_path:
        return
    
    # Convert certificate
    cert_file, cert_hash = convert_cert(cert_path, openssl_path)
    if not cert_file or not cert_hash:
        return
    
    # Connect to device
    if not check_device_connection(adb_path):
        return
    
    # Install certificate
    if install_certificate(adb_path, cert_file, cert_hash):
        logger.success("="*60)
        logger.success("CERTIFICATE INSTALLED SUCCESSFULLY!".center(60))
        logger.success("="*60)
        logger.info("You can now intercept HTTPS traffic in Burp Suite")
        logger.info("Test with: adb shell curl -k https://example.com")
    else:
        logger.error("Certificate installation failed")

# --- CLI Handling ---
def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description=f"burpDrop v{VERSION} - Android Burp Certificate Installer",
        add_help=False
    )
    parser.add_argument(
        'command', 
        nargs='?', 
        default='install',
        help='Command to execute (install, logs, help)'
    )
    parser.add_argument(
        '--version', 
        action='version', 
        version=f'burpDrop v{VERSION}',
        help='Show version information'
    )
    parser.add_argument(
        '--help', 
        action='store_true',
        help='Show help message'
    )
    return parser.parse_args()

# --- Main Application ---
def main():
    """Main application entry point"""
    args = parse_arguments()
    
    # Show version at launch
    logger.info(f"Starting burpDrop v{VERSION}")
    
    # Handle help and version
    if args.help or args.command == 'help':
        print(HELP_TEXT)
        return
    
    # Load config
    config = load_config()
    
    # Handle commands
    if args.command == 'install':
        logger.info("Starting certificate installation")
        install_certificate_flow(config)
    elif args.command == 'logs':
        logger.info("Showing log files")
        view_logs()
    else:
        logger.error(f"Unknown command: {args.command}")
        print(HELP_TEXT)

if __name__ == "__main__":
    main()