# logger_config.py
import logging
import os
from logging.handlers import RotatingFileHandler

def get_logger(name: str, log_level=logging.INFO, log_dir="logs", log_file="app.log"):
    """
    Returns a logger instance with console and file handlers.
    
    Args:
        name (str): Logger name (usually __name__).
        log_level (int): Logging level (default: INFO).
        log_dir (str): Directory to store log files.
        log_file (str): Log file name.
    """
    
    # Ensure log directory exists
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Prevent duplicate handlers if re-imported
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_format = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_format)

        # File handler (rotating logs, 5 MB per file, keep 5 backups)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, log_file), maxBytes=5 * 1024 * 1024, backupCount=5
        )
        file_handler.setLevel(log_level)
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
        )
        file_handler.setFormatter(file_format)

        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
