import logging

_log_file_cleared = False

def get_logger(name):
    """
    Returns a configured logger with the given name.
    """
    global _log_file_cleared
    logger = logging.getLogger(name)
    
    # Only configure if it doesn't already have handlers to avoid duplicate logs
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Clear the file only on the very first time a logger is created in this run
        file_mode = 'w' if not _log_file_cleared else 'a'
        _log_file_cleared = True
        
        # Create file handler for everything (INFO level and above)
        file_handler = logging.FileHandler('app.log', mode=file_mode)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler for critical errors only
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.CRITICAL)
        
        # Create formatter and add it to the handlers
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)-8s] [%(name)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add the handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger
