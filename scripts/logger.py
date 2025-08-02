import datetime
import os
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLOR_ENABLED = True
except ImportError:
    COLOR_ENABLED = False

# --- Logger Class ---
class Logger:
    def __init__(self, log_dir):
        self.log_file = os.path.join(log_dir, f"burpdrop_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        os.makedirs(log_dir, exist_ok=True)
    
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