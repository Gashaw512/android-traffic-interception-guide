#!/usr/bin/env python3

import os
import subprocess
import platform
import datetime
import shutil
import sys
import atexit
import json

# --- Optional Libraries for Enhanced Experience ---
try:
    import tkinter as tk
    from tkinter import filedialog
    HAS_TK = True
except ImportError:
    HAS_TK = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from colorama import Fore, Style, init
    init(autoreset=True) # Initialize colorama for Windows compatibility
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False

# --- Configuration ---
# GitHub repository for update checks
REPO = "gashawkidanu/burpDrop"
LOCAL_VERSION = "1.1.0" # Current version of this script

# Base directory for the script, ensuring portability
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
TEMP_CERT_DIR = os.path.join(SCRIPT_DIR, "temp_cert")
DEVICE_CERT_DIR = "/system/etc/security/cacerts" # Android system certs directory

# Ensure log and temp directories exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TEMP_CERT_DIR, exist_ok=True)

# --- Global Tool Paths ---
ADB = shutil.which("adb")
OPENSSL = shutil.which("openssl")

# --- Logger Class for Consistent Output ---
class Logger:
    def __init__(self, log_dir):
        self.log_dir = log_dir
        self.log_file = os.path.join(self.log_dir, f"install-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.log")

    def _log(self, message, level="INFO", color=None):
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
        console_message = f"{timestamp} [{level}] {message}"
        file_message = f"{timestamp} [{level}] {message}"

        if HAS_COLORAMA and color:
            print(f"{color}{console_message}{Style.RESET_ALL}")
        else:
            print(console_message)

        with open(self.log_file, "a") as f:
            f.write(f"{file_message}\n")

    def info(self, message):
        self._log(message, "INFO", Fore.CYAN if HAS_COLORAMA else None)

    def success(self, message):
        self._log(f"✅ {message}", "SUCCESS", Fore.GREEN if HAS_COLORAMA else None)

    def error(self, message):
        self._log(f"❌ {message}", "ERROR", Fore.RED if HAS_COLORAMA else None)

    def warn(self, message):
        self._log(f"⚠️  {message}", "WARNING", Fore.YELLOW if HAS_COLORAMA else None)

# Initialize the logger
logger = Logger(LOG_DIR)

# --- Cleanup Function ---
def cleanup():
    """Removes temporary files and directories."""
    logger.info("🧹 Cleaning up temporary files...")
    if os.path.exists(TEMP_CERT_DIR):
        try:
            shutil.rmtree(TEMP_CERT_DIR)
            logger.success(f"Temporary directory '{TEMP_CERT_DIR}' removed.")
        except OSError as e:
            logger.error(f"Error removing temporary directory '{TEMP_CERT_DIR}': {e}")
    else:
        logger.warn(f"Temporary directory '{TEMP_CERT_DIR}' not found, no cleanup needed.")

# Register cleanup to run on script exit
atexit.register(cleanup)

# --- Dependency Checks ---
def check_dependencies():
    """Verifies that ADB and OpenSSL are installed and accessible."""
    logger.info("Verifying required dependencies (adb, openssl)...")
    missing_tools = []

    if not ADB:
        missing_tools.append("adb")
    if not OPENSSL:
        missing_tools.append("openssl")

    if missing_tools:
        logger.error(f"The following required tools are NOT found: {', '.join(missing_tools)}.")
        logger.error("Please install them and ensure they are in your system's PATH.")
        logger.error("  - For ADB: Install Android SDK Platform-Tools (developer.android.com/studio/releases/platform-tools)")
        logger.error("  - For OpenSSL: Install from your OS package manager (e.g., 'sudo apt install openssl' on Debian/Ubuntu, 'brew install openssl' on macOS/Homebrew)")
        sys.exit(1)
    else:
        logger.success("All required dependencies (adb, openssl) found.")

# --- Update Checker ---
def check_for_updates():
    """Checks for the latest version of the script on GitHub."""
    logger.info("Checking for updates to burpDrop...")

    if not HAS_REQUESTS:
        logger.warn("Python 'requests' library not found. Skipping update check. Install with 'pip install requests'.")
        return

    try:
        response = requests.get(f"https://api.github.com/repos/{REPO}/releases/latest", timeout=5)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        latest_release = response.json()
        latest_version = latest_release.get("tag_name")

        if not latest_version:
            logger.warn("Could not retrieve latest version from GitHub. 'tag_name' not found in API response.")
            return

        if latest_version != LOCAL_VERSION:
            logger.warn(f"🚨 A new version is available: {latest_version} (You are using {LOCAL_VERSION})")
            logger.warn(f"📦 Please visit: https://github.com/{REPO}/releases/latest to download the latest version.")
        else:
            logger.success(f"You are running the latest version: {LOCAL_VERSION}")

    except requests.exceptions.RequestException as e:
        logger.warn(f"Could not check for updates (network issue or API rate limit?): {e}")
    except json.JSONDecodeError:
        logger.warn("Failed to parse GitHub API response. Unexpected format.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during update check: {e}")

# --- Certificate File Selection ---
def browse_cert_file():
    """
    Attempts to open a GUI file dialog for certificate selection.
    Falls back to OS-specific CLI tools if Tkinter is not available.
    """
    if HAS_TK:
        try:
            root = tk.Tk()
            root.withdraw() # Hide the main window
            file_path = filedialog.askopenfilename(
                title="Select Burp CA Certificate (.der)",
                filetypes=[("DER files", "*.der"), ("All files", "*.*")]
            )
            return file_path.strip('"') if file_path else None
        except Exception as e:
            logger.warn(f"Tkinter error: {e}. Falling back to CLI prompt.")
    
    # Fallback for Linux with Zenity
    if platform.system() == "Linux" and shutil.which("zenity"):
        try:
            result = subprocess.run(
                ['zenity', '--file-selection', '--title=Select Burp CA Certificate', '--file-filter=*.der'],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=True
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except subprocess.CalledProcessError:
            logger.warn("Zenity file selection failed. Falling back to CLI prompt.")
        except Exception as e:
            logger.warn(f"Error with Zenity: {e}. Falling back to CLI prompt.")

    # Fallback for macOS with osascript
    elif platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ['osascript', '-e', 'POSIX path of (choose file with prompt "Select Burp CA Certificate" of type {"der"})'],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            logger.warn("osascript file selection failed. Falling back to CLI prompt.")
        except Exception as e:
            logger.warn(f"Error with osascript: {e}. Falling back to CLI prompt.")

    return None # Fallback to CLI if all GUI methods fail

def get_cert_file():
    """Prompts the user for the certificate file path, trying GUI first."""
    cert_path = browse_cert_file()
    if not cert_path:
        logger.info("\n📂 Drag and drop your `.der` certificate into the terminal, then press Enter.")
        raw_input = input("📥 Certificate file path: ").strip()

        # Clean up wrapping quotes and escaped paths (common with drag-and-drop)
        cert_path = raw_input.strip().strip('"').strip("'").replace("\\ ", " ")
    
    if not cert_path or not os.path.isfile(cert_path):
        logger.error(f"File not found: '{cert_path}'. Please provide a valid path.")
        return None
    
    return os.path.abspath(cert_path)

# --- Certificate Conversion ---
def convert_der_to_hash(cert_path):
    """
    Converts a DER certificate to PEM, generates its subject hash,
    and renames the PEM file to the hashed name.
    """
    pem_file = os.path.join(TEMP_CERT_DIR, "burp.pem")

    try:
        logger.info("🔧 Converting DER to PEM...")
        subprocess.run(
            [OPENSSL, "x509", "-inform", "der", "-in", cert_path, "-out", pem_file],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        logger.success("Certificate converted to PEM.")

        logger.info("🔍 Generating subject hash...")
        result = subprocess.run(
            [OPENSSL, "x509", "-inform", "pem", "-subject_hash_old", "-in", pem_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        cert_hash = result.stdout.splitlines()[0].strip()
        hash_file = os.path.join(TEMP_CERT_DIR, f"{cert_hash}.0")
        
        os.rename(pem_file, hash_file)
        logger.success(f"Certificate prepared as '{cert_hash}.0'.")
        return hash_file, cert_hash
    except subprocess.CalledProcessError as e:
        logger.error(f"OpenSSL conversion or hashing failed: {e.stderr.strip()}")
        return None, None
    except OSError as e:
        logger.error(f"File system error during certificate conversion: {e}")
        return None, None

# --- ADB Operations ---
def adb_command(args, check_output=False):
    """
    Executes an ADB command.
    Returns stdout if successful, None on failure.
    """
    full_cmd = [ADB] + args
    try:
        result = subprocess.run(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True # Raise CalledProcessError for non-zero exit codes
        )
        if check_output:
            return result.stdout.strip()
        return True # Indicate success
    except subprocess.CalledProcessError as e:
        logger.error(f"ADB command failed: {' '.join(full_cmd)}")
        logger.error(f"Error: {e.stderr.strip()}")
        return None
    except FileNotFoundError:
        logger.error(f"ADB executable not found at '{ADB}'. Please ensure ADB is in your PATH.")
        return None

def ensure_device_ready():
    """Checks for connected Android device and waits if necessary."""
    logger.info("Checking for connected Android device...")
    retries = 5
    for i in range(retries):
        state = adb_command(["get-state"], check_output=True)
        if state == "device":
            logger.success("ADB device detected and ready.")
            return True
        elif state == "offline":
            logger.warn(f"Device is offline. Retrying in 5 seconds... ({i+1}/{retries})")
        else:
            logger.warn(f"No ADB device found or device state is '{state}'. Ensure emulator/device is running. Retrying in 5 seconds... ({i+1}/{retries})")
        
        if i < retries - 1: # Don't sleep on the last retry
            import time
            time.sleep(5)
    
    logger.error("Failed to detect a ready ADB device after multiple attempts.")
    return False

def adb_root_remount():
    """Attempts to get root access and remount /system."""
    logger.info("Attempting to get root access via 'adb root'...")
    if not adb_command(["root"]):
        logger.error("Failed to get root access. This device might not be rooted or 'adb root' is not supported.")
        logger.error("Please ensure your device is rooted and 'adb root' works manually, then try again.")
        return False
    logger.success("Root access obtained.")

    logger.info("Attempting to remount /system partition as read-write...")
    if not adb_command(["remount"]):
        logger.error("Failed to remount /system as read-write.")
        logger.error("You might need to disable verity or flash a custom recovery. Try 'adb disable-verity' and reboot, then try again.")
        return False
    logger.success("/system partition remounted successfully (read-write).")
    return True

def backup_remote_cert(hash_name):
    """Backs up an existing certificate on the device if it exists."""
    device_cert_path = f"{DEVICE_CERT_DIR}/{hash_name}.0"
    logger.info(f"Checking for existing certificate '{device_cert_path}' on device for backup...")

    # Use 'ls' to check for file existence without error if not found
    ls_result = subprocess.run([ADB, "shell", f"ls {device_cert_path}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if ls_result.returncode == 0: # File exists
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{device_cert_path}.bak.{timestamp}"
        logger.warn(f"Existing certificate found. Backing up to '{backup_file}'...")
        if adb_command(["shell", f"cp {device_cert_path} {backup_file}"], check_output=False):
            logger.success("Backup created successfully.")
        else:
            logger.error("Failed to create backup of existing certificate.")
    else:
        logger.info("No existing certificate found on device. No backup needed.")

def install_cert_on_device(local_cert_file, hash_name):
    """Pushes the certificate to the device and sets permissions."""
    device_target_path = f"{DEVICE_CERT_DIR}/{hash_name}.0"

    logger.info(f"Pushing certificate '{local_cert_file}' to device at '{device_target_path}'...")
    if not adb_command(["push", local_cert_file, device_target_path]):
        return False
    logger.success("Certificate pushed successfully.")

    logger.info(f"Setting permissions (chmod 644) for '{device_target_path}'...")
    if not adb_command(["shell", f"chmod 644 {device_target_path}"]):
        return False
    logger.success("Permissions set to 644.")
    return True

def reboot_device_and_wait():
    """Reboots the device and waits for it to come back online."""
    logger.info("Rebooting Android device...")
    if not adb_command(["reboot"]):
        return False
    logger.info("Device is rebooting. Waiting for it to come back online (this may take a minute or two)...")
    
    # adb wait-for-device will block until device is online
    subprocess.run([ADB, "wait-for-device"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    logger.success("Device has rebooted and is back online.")
    return True

# --- Log Viewer ---
def show_logs():
    """Displays recent log files and allows viewing a specific log."""
    logger.info("--- Viewing Logs ---")
    if not os.path.isdir(LOG_DIR) or not os.listdir(LOG_DIR):
        logger.warn("No logs available yet.")
        return

    log_files = sorted([f for f in os.listdir(LOG_DIR) if os.path.isfile(os.path.join(LOG_DIR, f))], reverse=True)
    
    if not log_files:
        logger.warn("No log files found.")
        return

    print("\nRecent log files (last 5):")
    for i, log_file in enumerate(log_files[:5]):
        print(f"  {i+1}. {log_file}")
    print("---------------------")

    while True:
        choice = input("Enter the number or filename of the log you wish to view (or 'b' to go back): ").strip()
        if choice.lower() == 'b':
            return

        try:
            log_index = int(choice) - 1
            if 0 <= log_index < len(log_files):
                logfile_to_view = log_files[log_index]
            else:
                logger.warn("Invalid number. Please try again.")
                continue
        except ValueError:
            # Not a number, assume it's a filename
            logfile_to_view = choice.strip().strip('"').strip("'")
            if not os.path.isfile(os.path.join(LOG_DIR, logfile_to_view)):
                logger.warn(f"Log file '{logfile_to_view}' not found in '{LOG_DIR}'. Please try again.")
                continue
        
        full_log_path = os.path.join(LOG_DIR, logfile_to_view)
        logger.info(f"Displaying log: '{logfile_to_view}'")
        
        # Use 'less' or 'more' for viewing large log files, or just print for smaller ones
        if platform.system() == "Windows":
            subprocess.run(["more", full_log_path], check=False)
        else:
            subprocess.run(["less", full_log_path], check=False)
        break


# --- Main Application Logic ---
def main():
    """Main function to run the burpDrop application."""
    check_dependencies()
    check_for_updates() # Check for updates at startup

    while True:
        print("\n📜 burpDrop – Cross-Platform Android CA Installer")
        print("1️⃣  Install Certificate")
        print("2️⃣  Show Logs")
        print("3️⃣  Exit")
        choice = input("👉 Choose an option: ").strip()

        if choice == "1":
            cert_path = get_cert_file()
            if cert_path:
                cert_file, hash_name = convert_der_to_hash(cert_path)
                if cert_file and hash_name:
                    logger.info("--- Starting Certificate Installation ---")
                    if not ensure_device_ready():
                        continue
                    if not adb_root_remount():
                        continue
                    backup_remote_cert(hash_name)
                    if not install_cert_on_device(cert_file, hash_name):
                        continue
                    if not reboot_device_and_wait():
                        continue
                    logger.success("🎉 Certificate installation complete. Please verify on your device.")
                else:
                    logger.error("Certificate conversion failed. Aborting installation.")
            else:
                logger.error("No valid certificate file selected. Aborting installation.")
        elif choice == "2":
            show_logs()
        elif choice == "3":
            logger.info("👋 Exiting burpDrop. Happy Testing!")
            break
        else:
            logger.warn("❌ Invalid option. Please choose 1, 2, or 3.")

if __name__ == "__main__":
    main()
