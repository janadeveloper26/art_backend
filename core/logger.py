import logging

logger = logging.getLogger("art_backend")

def log_info(message: str):
    logger.info(message)

def log_error(message: str, exc_info=True):
    logger.error(message, exc_info=exc_info)
