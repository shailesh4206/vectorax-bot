import logging
import sys
from logging.handlers import RotatingFileHandler
import os
from config import LOG_LEVEL

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

def setup_logger(name='vectorax'):
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL or 'INFO'))

    # Console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    try:
        # Windows: wrap stdout with utf-8
        console_handler.stream = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
    except Exception:
        # fallback if not possible
        pass
    logger.addHandler(console_handler)

    # File handler with rotation (UTF-8)
    file_handler = RotatingFileHandler(
        'logs/vectorax.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'  # important
    )
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger

logger = setup_logger()