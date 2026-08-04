# utils/logger.py
import os
import logging

LOG_DIR = os.path.expanduser("~/dirt-touch/logs")
LOG_FILE = os.path.join(LOG_DIR, "launcher.log")

def setup_logger():
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # Also log to stdout for debugging
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)

def log_info(msg: str):
    logging.info(msg)

def log_error(msg: str):
    logging.error(msg)