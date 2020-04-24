import logging

from config import APP


def get_fmt():
    return logging.Formatter(fmt=APP.LOG_FORMAT)


def get_handler():
    handler = logging.StreamHandler()
    handler.setFormatter(get_fmt())
    return handler


def get_logger(name):
    for lib in ["requests", "urllib3"]:
        logging.getLogger(lib).setLevel(APP.LOG_LEVEL)

    logger = logging.getLogger(name)
    logger.setLevel(APP.LOG_LEVEL)
    logger.addHandler(get_handler())

    return logger
