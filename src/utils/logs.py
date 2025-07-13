import os, logging
from variables import Variables, StaticVariables

from config import Config

def setup_logger():
    fmt = "[{asctime}] [{levelname}] [{module}.{funcName}:{lineno}]: {message}"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt, style="{")

    # setup handlers #
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    file_handler = None
    if Config.LOGGING_ENABLED: 
        file_handler = logging.FileHandler(
            filename=os.path.join(StaticVariables.logs_path, Variables.session_id + ".log"),
            encoding="utf-8",
            mode="a"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.NOTSET)
    
    # logger #
    logging.root.handlers.clear()

    logger = logging.getLogger()
    logger.setLevel(logging.NOTSET)

    if file_handler: logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # loaded #
    logging.debug("Logger loaded!")

def disable_spammy_loggers():
    logging.info("Disabling spammy loggers...")

    # disable console spam #
    all_loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    for logger in all_loggers:
        if logger.name.startswith("comtypes") or logger.name.startswith("watchdog.observers.inotify"):
            logging.info(f"  - {logger.name} disabled.")
            logger.setLevel(logging.ERROR)