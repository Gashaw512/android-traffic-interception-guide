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
VERSION = "1.5.0"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
TEMP_CERT_DIR = os.path.join(SCRIPT_DIR, "temp_cert")
DEVICE_CERT_DIR = "/system/etc/security/cacerts"
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
ADB_COMMON_PATHS_WIN = [
    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'platform-tools', 'adb.exe'),
    os.path.join('C:\\', 'platform-tools', 'adb.exe')
]
ADB_COMMON_PATHS_NIX = [
    '/usr/bin/adb',
    '/usr/local/bin/adb',
    os.path.join(os.environ.get('HOME', ''), 'Library', 'Android', 'sdk', 'platform-tools', 'adb')
]
OPENSSL_COMMON_PATHS_WIN = [
    os.path.join('C:\\', 'Program Files', 'OpenSSL-Win64', 'bin', 'openssl.exe'),
    os.path.join('C:\\', 'Program Files (x82)', 'OpenSSL-Win32', 'bin', 'openssl.exe')
]

HELP_TEXT = """
BurpDrop - Android Burp Certificate Installer

Commands:
  install   Install Burp certificate on Android device
  config    Configure paths for adb and openssl
  logs      View installation logs
  help      Show this help message

Options:
  --version  Show version information
  --help     Show help

Example:
  burpdrop install
  burpdrop install --dry-run
  burpdrop config --adb "C:\\path\\to\\adb.exe"
"""

# --- Logger Class ---
class Logger:
    def __init__(self):
        self.log_file = os.path.join(LOG_DIR, f"burpdrop_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        os.makedirs(LOG_DIR, exist_ok=True)
        
    def log(self, message, level="INFO", color=None):
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
        log_entry = f"{timestamp} [{level}] {message}"
        
        if COLOR_ENABLED and color:
            print(f"{color}{log_entry}{Style.RESET_ALL}")
        else:
            print(log_entry)
        
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

logger = Logger()

def cleanup():
    if os.path.exists(TEMP_CERT_DIR):
        try:
            shutil.rmtree(TEMP_CERT_DIR)
            logger.info("Cleaned temporary files")
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")

atexit.register(cleanup)

def load_config():
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

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        logger.success(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")

def get_tool_path(tool_name, config):
    config_path = config.get(f"{tool_name}_path")
    if config_path and os.path.exists(config_path):
        return config_path
    
    path_path = shutil.which(tool_name)
    if path_path:
        return path_path
        
    logger.warn(f"'{tool_name}' not found in PATH or config. Checking common installation directories...")
    common_paths = []
    if platform.system() == 'Windows':
        if tool_name == 'adb':
            common_paths = ADB_COMMON_PATHS_WIN
        elif tool_name == 'openssl':
            common_paths = OPENSSL_COMMON_PATHS_WIN
    else:
        if tool_name == 'adb':
            common_paths = ADB_COMMON_PATHS_NIX

    for path in common_paths:
        if os.path.exists(path):
            logger.info(f"Found '{tool_name}' at a common location: {path}")
            return path
    
    logger.error(f"'{tool_name}' executable not found.")
    logger.error(f"Please install it and add it to your system's PATH, or use the 'burpdrop config' command to specify its location.")
    return None

def get_cert_file():
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
    try:
        os.makedirs(TEMP_CERT_DIR, exist_ok=True)
        
        logger.info("Converting certificate format...")
        pem_file = os.path.join(TEMP_CERT_DIR, "burp.pem")
        os.makedirs(os.path.dirname(pem_file), exist_ok=True)
        
        subprocess.run(
            [openssl_path, "x509", "-inform", "der", "-in", cert_path, "-out", pem_file],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.progress("Conversion progress", 1, 3)
        
        result = subprocess.run(
            [openssl_path, "x509", "-inform", "pem", "-subject_hash_old", "-in", pem_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        cert_hash = result.stdout.splitlines()[0].strip()
        logger.progress("Processing certificate", 2, 3)
        
        hash_file = os.path.join(TEMP_CERT_DIR, f"{cert_hash}.0")
        os.rename(pem_file, hash_file)
        logger.progress("Finalizing conversion", 3, 3)
        logger.success(f"Certificate prepared: {cert_hash}.0")
        
        return hash_file, cert_hash
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode().strip() if isinstance(e.stderr, bytes) else e.stderr.strip()
        logger.error(f"OpenSSL command failed: {error_msg}")
        return None, None
    except Exception as e:
        logger.error(f"Certificate processing error: {str(e)}")
        logger.info("Please check your certificate file and try again")
        return None, None

def run_adb_command(adb_path, command):
    try:
        result = subprocess.run(
            [adb_path] + command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except FileNotFoundError:
        logger.error("ADB executable not found. Check your config.json")
        return None, None, 1

def check_device_connection(adb_path):
    logger.info("Checking device connection...")
    state, _, _ = run_adb_command(adb_path, ["get-state"])
    if state == "device":
        logger.success("Device connected and ready")
        return True
    
    logger.error("No device found or not ready.")
    logger.info("Troubleshooting:")
    logger.info("1. Ensure your emulator is running or device is connected via USB.")
    logger.info("2. If a physical device, enable 'USB debugging' in Developer Options.")
    logger.info("3. Check for multiple connected devices with 'adb devices'.")
    return False

def install_certificate(adb_path, cert_file, cert_hash, dry_run=False):
    if dry_run:
        logger.warn("DRY RUN: No changes will be made to the device.")

    steps = 5
    current_step = 1
    
    logger.info("Getting root access...")
    if dry_run:
        logger.info("[DRY RUN] Would run: adb root")
    else:
        run_adb_command(adb_path, ["root"])
    logger.progress("Installation progress", current_step, steps)
    current_step += 1
    time.sleep(1)
    
    logger.info("Remounting filesystem...")
    if dry_run:
        logger.info("[DRY RUN] Would run: adb remount")
        logger.success("Filesystem remounted as read-write (simulated)")
    else:
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
    
    logger.info("Pushing certificate to device...")
    remote_path = f"{DEVICE_CERT_DIR}/{cert_hash}.0"
    if dry_run:
        logger.info(f"[DRY RUN] Would run: adb push {cert_file} {remote_path}")
    else:
        stdout, stderr, returncode = run_adb_command(adb_path, ["push", cert_file, remote_path])
        if returncode != 0:
            logger.error("Failed to push certificate.")
            logger.error("Error: " + stderr)
            return False
    logger.progress("Installation progress", current_step, steps)
    current_step += 1
    
    logger.info("Setting permissions...")
    if dry_run:
        logger.info(f"[DRY RUN] Would run: adb shell chmod 644 {remote_path}")
    else:
        stdout, stderr, returncode = run_adb_command(adb_path, ["shell", f"chmod 644 {remote_path}"])
        if returncode != 0:
            logger.error("Failed to set permissions.")
            logger.error("Error: " + stderr)
            return False
    logger.progress("Installation progress", current_step, steps)
    current_step += 1
    
    logger.info("Rebooting device...")
    if dry_run:
        logger.info("[DRY RUN] Would run: adb reboot")
        logger.success("Device rebooting (simulated)")
        logger.info("You can now connect to your device after it reboots.")
    else:
        run_adb_command(adb_path, ["reboot"])
        logger.info("Device rebooting. Please wait...")
        run_adb_command(adb_path, ["wait-for-device"])
        logger.success("Device reconnected after reboot")
    logger.progress("Installation progress", current_step, steps)
    
    return True

def view_logs():
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

def install_certificate_flow(config, dry_run):
    adb_path = get_tool_path("adb", config)
    openssl_path = get_tool_path("openssl", config)
    
    if not adb_path or not openssl_path:
        logger.error("Required tools not found. Please run 'burpdrop config --help' for assistance.")
        return
    
    cert_path = get_cert_file()
    if not cert_path:
        return
    
    cert_file, cert_hash = convert_cert(cert_path, openssl_path)
    if not cert_file or not cert_hash:
        return
    
    if not check_device_connection(adb_path):
        return
    
    if install_certificate(adb_path, cert_file, cert_hash, dry_run):
        logger.success("="*60)
        if dry_run:
            logger.success("DRY RUN COMPLETE: No changes were made.".center(60))
        else:
            logger.success("CERTIFICATE INSTALLED SUCCESSFULLY!".center(60))
        logger.success("="*60)
        logger.info("You can now intercept HTTPS traffic in Burp Suite")
        logger.info("Test with: adb shell curl -k https://example.com")
    else:
        logger.error("Certificate installation failed")

def configure_flow(args, config):
    new_config = config.copy()
    
    if args.adb:
        if os.path.exists(args.adb):
            new_config['adb_path'] = args.adb
            logger.success(f"ADB path set to: {args.adb}")
        else:
            logger.error(f"Path not found: {args.adb}")

    if args.openssl:
        if os.path.exists(args.openssl):
            new_config['openssl_path'] = args.openssl
            logger.success(f"OpenSSL path set to: {args.openssl}")
        else:
            logger.error(f"Path not found: {args.openssl}")
    
    if not args.adb and not args.openssl:
        logger.info("Current configuration:")
        if new_config:
            for key, value in new_config.items():
                logger.info(f"- {key}: {value}")
        else:
            logger.info("No paths configured yet.")
        logger.info("\nTo set paths, use: burpdrop config --adb \"/path/to/adb\"")
    
    save_config(new_config)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description=f"burpDrop v{VERSION} - Android Burp Certificate Installer",
        add_help=False
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Install command
    install_parser = subparsers.add_parser('install', help='Install Burp certificate on an Android device')
    install_parser.add_argument('--dry-run', action='store_true', help='Simulate the installation without modifying the device.')

    # Config command
    config_parser = subparsers.add_parser('config', help='Configure paths for adb and openssl')
    config_parser.add_argument('--adb', help='Path to the ADB executable')
    config_parser.add_argument('--openssl', help='Path to the OpenSSL executable')

    # Logs command
    logs_parser = subparsers.add_parser('logs', help='View installation logs')

    # Global options
    parser.add_argument('--version', action='version', version=f'burpDrop v{VERSION}', help='Show version information')
    parser.add_argument('--help', action='store_true', help='Show help message')

    return parser.parse_args()

def main():
    args = parse_arguments()
    
    logger.info(f"Starting burpDrop v{VERSION}")
    
    if args.help:
        print(HELP_TEXT)
        return
    
    config = load_config()
    
    if args.command == 'install':
        install_certificate_flow(config, args.dry_run)
    elif args.command == 'config':
        configure_flow(args, config)
    elif args.command == 'logs':
        view_logs()
    else:
        print(HELP_TEXT)

if __name__ == "__main__":
    main()