import logging
import os
from logging.handlers import RotatingFileHandler
import config

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def get_logger(name):
    """
    Returns a configured logger with the given name.
    
    Args:
        name: The name for the logger instance.
        
    Returns:
        A configured logging.Logger object.
    """
    logger = logging.getLogger(name)
    
    # Only configure if it doesn't already have handlers to avoid duplicate logs
    if not logger.handlers:
        # Determine log level from config
        env_level = config.LOG_LEVEL.upper()
        log_level = getattr(logging, env_level, logging.INFO)
        logger.setLevel(log_level)
        
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)-8s] [%(name)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # Create main rotating file handler (5MB max, keep 5 backups)
        main_log_path = os.path.join(LOG_DIR, 'pipeline.log')
        file_handler = RotatingFileHandler(main_log_path, maxBytes=5 * 1024 * 1024, backupCount=5, delay=True)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # Create rotating error file handler (5MB max, keep 5 backups)
        error_log_path = os.path.join(LOG_DIR, 'errors.log')
        error_handler = RotatingFileHandler(error_log_path, maxBytes=5 * 1024 * 1024, backupCount=5, delay=True)
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(formatter)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        
        # Add the handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        logger.addHandler(console_handler)
        
    return logger
