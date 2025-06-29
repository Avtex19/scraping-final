import logging
import os
from logging.handlers import QueueHandler


def setup_logger(name, log_file=None, log_level=logging.INFO, log_queue=None):
    """
    Create and return a logger with optional QueueHandler for multiprocessing.

    Args:
        name (str): Logger name.
        log_file (str): Path to log file.
        log_level (int): Logging level.
        log_queue (Queue): If provided, use QueueHandler for multiprocessing-safe logging.
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.propagate = False  # Prevent double logging

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler()
    console_format = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # Choose handler based on whether we're in multiprocessing mode
    if log_queue:
        # Use QueueHandler for multiprocessing-safe logging
        handler = QueueHandler(log_queue)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    elif log_file:
        # Use FileHandler with UTF-8 encoding for emoji support
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger
