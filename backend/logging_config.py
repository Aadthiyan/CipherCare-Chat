import logging
import json
import sys
from datetime import datetime

class CleanFormatter(logging.Formatter):
    """Clean, readable formatter with color support for errors"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Color for level
        level_color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Get message
        message = record.getMessage()
        
        # For ERROR and CRITICAL, add more details
        if record.levelname in ['ERROR', 'CRITICAL']:
            if record.exc_info:
                exception_text = self.formatException(record.exc_info)
                return f"{level_color}[{timestamp}] {record.levelname}{reset} {message}\n{level_color}{exception_text}{reset}"
            else:
                return f"{level_color}[{timestamp}] {record.levelname} [{record.module}:{record.lineno}]{reset}\n{message}"
        
        # For INFO and DEBUG, keep it simple
        return f"[{timestamp}] {level_color}{record.levelname}{reset} {message}"

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logging():
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove all existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console Handler with clean formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CleanFormatter())
    logger.addHandler(console_handler)
    
    # File Handler with JSON formatter for detailed logs
    file_handler = logging.FileHandler("backend/app.log")
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Silence noisy libraries
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("uvicorn.error").propagate = False
