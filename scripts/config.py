import json
import os
import platform
from logger import Logger

logger = Logger(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"))

# --- Constants ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
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
    os.path.join('C:\\', 'Program Files (x86)', 'OpenSSL-Win32', 'bin', 'openssl.exe')
]

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
    import shutil
    
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