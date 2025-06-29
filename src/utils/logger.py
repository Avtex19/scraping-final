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

    if log_queue:
        handler = QueueHandler(log_queue)
    else:
        handler = logging.FileHandler(log_file) if log_file else logging.StreamHandler()

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger
