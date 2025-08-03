import os
import subprocess
import time
from collections import namedtuple
from .logger import Logger

logger = Logger(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"))

# --- Constants ---
DEVICE_CERT_DIR = "/system/etc/security/cacerts"
TEMP_CERT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_cert")
MAGISK_CERT_DIR = "/data/adb/modules/system_ca_cert_mojito/system/etc/security/cacerts"

# --- Pythonic Improvement ---
AdbCommandResult = namedtuple('AdbCommandResult', ['stdout', 'stderr', 'returncode'])

def run_adb_command(adb_path, command):
    try:
        result = subprocess.run(
            [adb_path] + command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return AdbCommandResult(result.stdout.strip(), result.stderr.strip(), result.returncode)
    except FileNotFoundError:
        logger.error("ADB executable not found. Check your config.json")
        return AdbCommandResult(None, None, 1)

def check_device_connection(adb_path):
    logger.info("Checking device connection...")
    result = run_adb_command(adb_path, ["get-state"])
    if result.stdout == "device":
        logger.success("Device connected and ready")
        return True
    
    logger.error("No device found or not ready.")
    logger.info("Troubleshooting:")
    logger.info("1. Ensure your emulator is running or device is connected via USB.")
    logger.info("2. If a physical device, enable 'USB debugging' in Developer Options.")
    logger.info("3. Check for multiple connected devices with 'adb devices'.")
    return False

def get_android_version(adb_path):
    """
    Retrieves the Android version from the connected device.
    """
    logger.info("Detecting Android version...")
    result = run_adb_command(adb_path, ["shell", "getprop ro.build.version.release"])
    if result.returncode == 0 and result.stdout:
        version = result.stdout.strip()
        logger.info(f"Android version detected: {version}")
        return version
    else:
        logger.warn("Could not determine Android version.")
        return None

def install_certificate(adb_path, cert_file, cert_hash, dry_run=False, is_magisk=False):
    if dry_run:
        logger.warn("DRY RUN: No changes will be made to the device.")

    if is_magisk:
        logger.info("Magisk mode selected. Installing certificate to systemless path.")
        result = run_adb_command(adb_path, ["shell", "test -d " + MAGISK_CERT_DIR])
        if result.returncode != 0:
            logger.error("Magisk systemless module 'system_ca_cert_mojito' not found.")
            logger.info("Please install it from Magisk's download section or a trusted source and try again.")
            return False
        remote_path = f"{MAGISK_CERT_DIR}/{cert_hash}.0"
    else:
        logger.info("Standard root mode selected.")
        remote_path = f"{DEVICE_CERT_DIR}/{cert_hash}.0"

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
        result = run_adb_command(adb_path, ["remount"])
        if result.returncode != 0 or "remount succeeded" not in result.stdout.lower():
            logger.error("Failed to remount filesystem.")
            logger.error("Error: " + result.stderr)
            logger.info("This can happen if the device is not rooted or is protected by dm-verity.")
            logger.info("Try running 'adb disable-verity && adb reboot' manually before using burpdrop.")
            return False
        logger.success("Filesystem remounted as read-write")
    logger.progress("Installation progress", current_step, steps)
    current_step += 1
    
    logger.info("Pushing certificate to device...")
    if dry_run:
        logger.info(f"[DRY RUN] Would run: adb push {cert_file} {remote_path}")
    else:
        result = run_adb_command(adb_path, ["push", cert_file, remote_path])
        if result.returncode != 0:
            logger.error("Failed to push certificate.")
            logger.error("Error: " + result.stderr)
            return False
    logger.progress("Installation progress", current_step, steps)
    current_step += 1
    
    logger.info("Setting permissions...")
    if dry_run:
        logger.info(f"[DRY RUN] Would run: adb shell chmod 644 {remote_path}")
    else:
        result = run_adb_command(adb_path, ["shell", f"chmod 644 {remote_path}"])
        if result.returncode != 0:
            logger.error("Failed to set permissions.")
            logger.error("Error: " + result.stderr)
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