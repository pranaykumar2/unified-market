import logging
import sys
from pathlib import Path
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for Windows support
init(autoreset=True)

# Define custom log levels globally
FEED_LEVEL = 22
SENT_LEVEL = 23
SCAN_LEVEL = 24

# Add custom level names
logging.addLevelName(FEED_LEVEL, 'FEED')
logging.addLevelName(SENT_LEVEL, 'SENT')
logging.addLevelName(SCAN_LEVEL, 'SCAN')

# Add custom methods to logging.Logger class so all loggers have them
def feed(self, message, *args, **kwargs):
    if self.isEnabledFor(FEED_LEVEL):
        self._log(FEED_LEVEL, message, args, **kwargs)

def sent(self, message, *args, **kwargs):
    if self.isEnabledFor(SENT_LEVEL):
        self._log(SENT_LEVEL, message, args, **kwargs)

def scan(self, message, *args, **kwargs):
    if self.isEnabledFor(SCAN_LEVEL):
        self._log(SCAN_LEVEL, message, args, **kwargs)

logging.Logger.feed = feed
logging.Logger.sent = sent
logging.Logger.scan = scan


class CleanFormatter(logging.Formatter):
    """Custom formatter with clean | separator format"""
    
    # Level name mappings with colors
    LEVEL_COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
        'FEED': Fore.BLUE,
        'SENT': Fore.GREEN,
        'SCAN': Fore.MAGENTA,
    }
    
    def format(self, record):
        # Get timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Get level name (handle custom levels)
        level_name = record.levelname
        
        # Color for level
        level_color = self.LEVEL_COLORS.get(level_name, Fore.WHITE)
        
        # Strip Rich markup tags from message
        import re
        message = record.getMessage()
        message = re.sub(r'\[/?(?:bold|cyan|green|yellow|red|magenta|blue)(?:\s+\w+)?\]', '', message)
        
        # Format: [HH:MM:SS] ▕ LEVEL ▏ Message
        formatted = (
            f"{Fore.WHITE}[{timestamp}] "
            f"▕ {level_color}{level_name:^6}{Style.RESET_ALL} ▏ "
            f"{message}"
        )
        
        return formatted


def setup_logger(name: str, log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """
    Setup a standardized logger with clean | separator format.
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # --- Console Handler with Clean Format ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CleanFormatter())
    logger.addHandler(console_handler)
    
    # --- File Handler (Technical) ---
    if log_file:
        file_formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        if log_file:
             try:
                 Path(log_file).parent.mkdir(parents=True, exist_ok=True)
                 file_handler = logging.FileHandler(log_file, encoding='utf-8')
                 file_handler.setFormatter(file_formatter)
                 logger.addHandler(file_handler)
             except Exception:
                 pass
        
    # Suppress verbose logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return logger
