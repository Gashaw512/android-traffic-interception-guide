#!/usr/bin/env python3
import os
import argparse
import sys
import atexit
from logger import Logger
from config import load_config, save_config, get_tool_path
from cert_handler import get_cert_file, convert_cert
from adb_client import check_device_connection, install_certificate, TEMP_CERT_DIR, get_android_version

# --- Constants ---
VERSION = "1.1.0"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
HELP_TEXT = f"""
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
  burpdrop install --magisk
  burpdrop install --dry-run
  burpdrop config --adb "C:\\path\\to\\adb.exe"
"""

logger = Logger(LOG_DIR)

def cleanup():
    if os.path.exists(TEMP_CERT_DIR):
        try:
            import shutil
            shutil.rmtree(TEMP_CERT_DIR)
            logger.info("Cleaned temporary files")
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")

atexit.register(cleanup)

def install_certificate_flow(config, dry_run, is_magisk):
    adb_path = get_tool_path("adb", config)
    openssl_path = get_tool_path("openssl", config)
    
    if not adb_path or not openssl_path:
        logger.error("Required tools not found. Please run 'burpdrop config --help' for assistance.")
        return
    
    if not check_device_connection(adb_path):
        return

    # Check Android version for user guidance
    android_version = get_android_version(adb_path)
    if android_version:
        try:
            if float(android_version) >= 7.0:
                logger.warn(f"Android {android_version} is detected. Note that certificate pinning is common on this version.")
                logger.warn("This tool only installs the CA certificate. You may need a tool like Frida to bypass pinning.")
        except ValueError:
            logger.warn(f"Could not parse Android version: {android_version}")
    
    cert_path = get_cert_file()
    if not cert_path:
        return
    
    cert_file, cert_hash = convert_cert(cert_path, openssl_path)
    if not cert_file or not cert_hash:
        return
    
    if install_certificate(adb_path, cert_file, cert_hash, dry_run, is_magisk):
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

def view_logs():
    logs_dir = os.path.join(SCRIPT_DIR, "logs")
    if not os.path.exists(logs_dir) or not os.listdir(logs_dir):
        logger.info("No log files available")
        return
    
    logs = [f for f in os.listdir(logs_dir) if f.startswith('burpdrop_')]
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
            log_file = os.path.join(logs_dir, logs[index])
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

def parse_arguments():
    parser = argparse.ArgumentParser(
        description=f"burpDrop v{VERSION} - Android Burp Certificate Installer",
        add_help=False
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Install command
    install_parser = subparsers.add_parser('install', help='Install Burp certificate on an Android device')
    install_parser.add_argument('--dry-run', action='store_true', help='Simulate the installation without modifying the device.')
    install_parser.add_argument('--magisk', action='store_true', help='Install certificate for Magisk systemless root.')

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
        install_certificate_flow(config, args.dry_run, args.magisk)
    elif args.command == 'config':
        configure_flow(args, config)
    elif args.command == 'logs':
        view_logs()
    else:
        print(HELP_TEXT)

if __name__ == "__main__":
    main()