import logging

def get_logger(name):
    """
    Returns a configured logger with the given name.
    """
    logger = logging.getLogger(name)
    
    # Only configure if it doesn't already have handlers to avoid duplicate logs
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create file handler for everything (INFO level and above)
        file_handler = logging.FileHandler('app.log')
        file_handler.setLevel(logging.INFO)
        
        # Create console handler for critical errors only
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.CRITICAL)
        
        # Create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add the handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger
