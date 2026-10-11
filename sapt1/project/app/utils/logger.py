import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app import config

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured Logger instance.
    Logs to both the console (sys.stdout/sys.stderr) and a rotating file.
    Ensures that parent directories for the log file are created.
    """
    logger = logging.getLogger(name)
    
    log_level_str = config.LOG_LEVEL
    level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(level)
    
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        log_file_path = Path(config.LOG_FILE)
        if not log_file_path.is_absolute():
            log_file_path = (config.BASE_DIR / log_file_path).resolve()
            
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            filename=str(log_file_path),
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger
