import logging

def setup_logger(name):
    logger = logging.getLogger(name)
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)
    return logger
