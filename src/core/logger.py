import logging
import os
from datetime import datetime
import config

# Initialize run variables globally so all loggers share the same timestamp
_run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
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

        # Create main file handler
        main_log_path = os.path.join(LOG_DIR, f'pipeline_{_run_timestamp}.log')
        file_handler = logging.FileHandler(main_log_path, mode='a')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # Create error file handler
        error_log_path = os.path.join(LOG_DIR, f'errors_{_run_timestamp}.log')
        error_handler = logging.FileHandler(error_log_path, mode='a')
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
