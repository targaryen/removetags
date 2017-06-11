import logging

def FCLogger(filepath, debug_level="INFO", name="logger"):
    log_level = logging.INFO
    if debug_level == "DEBUG":
        log_level = logging.DEBUG
    elif debug_level == "ERROR":
        log_level = logging.ERROR
    elif debug_level == "WARN":
        log_level = logging.WARN
    logger = logging.getLogger(name=name)
    logger.setLevel(debug_level)
    file_handler = logging.FileHandler(filepath)
    file_handler.setLevel(debug_level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(debug_level)
    formatter = logging.Formatter('[%(levelname)s]\t%(asctime)s \t%(name)s \t%(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

def ConsoleLogger(debug_level="INFO", name="logger"):
    log_level = logging.INFO
    if debug_level == "DEBUG":
        log_level = logging.DEBUG
    elif debug_level == "ERROR":
        log_level = logging.ERROR
    elif debug_level == "WARN":
        log_level = logging.WARN
    logger = logging.getLogger(name=name)
    logger.setLevel(debug_level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(debug_level)
    formatter = logging.Formatter('[%(levelname)s]\t%(asctime)s \t%(name)s \t%(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger
