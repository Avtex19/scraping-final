import logging
from logging.handlers import QueueHandler, QueueListener
import multiprocessing
import os

def get_log_queue():
    return multiprocessing.Manager().Queue()

def setup_worker_logger(log_queue):
    """Attach QueueHandler to worker's root logger"""
    handler = QueueHandler(log_queue)
    logger = logging.getLogger()
    logger.handlers = []  # Remove inherited handlers
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def start_logging_listener(log_queue, log_file='../logs/multiprocessing.log'):
    """Start logging listener in main process."""
    formatter = logging.Formatter('%(asctime)s - %(processName)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    listener = QueueListener(log_queue, file_handler)
    listener.start()
    return listener
