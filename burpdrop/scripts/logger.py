import os
import sys
import datetime
import colorama

class Logger:
    def __init__(self, log_dir):
        colorama.init(autoreset=True)
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = os.path.join(self.log_dir, f"burpdrop_{timestamp}.log")

    def _log(self, level, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        with open(self.log_file, "a", encoding='utf-8') as f:
            f.write(log_message + "\n")

    def info(self, message):
        self._log("INFO", f"{colorama.Fore.WHITE}{message}")

    def warn(self, message):
        self._log("WARNING", f"{colorama.Fore.YELLOW}⚠ {message}")

    def error(self, message):
        self._log("ERROR", f"{colorama.Fore.RED}❌ {message}")

    def success(self, message):
        self._log("SUCCESS", f"{colorama.Fore.GREEN}✓ {message}")
    
    def progress(self, message, current, total):
        bar_length = 20
        filled = int(bar_length * current / total)
        bar = '█' * filled + ' ' * (bar_length - filled)
        sys.stdout.write(f"\r[{message}] [{colorama.Fore.CYAN}{bar}{colorama.Style.RESET_ALL}] {current*100/total:.0f}%")
        sys.stdout.flush()
        if current == total:
            print("\n")