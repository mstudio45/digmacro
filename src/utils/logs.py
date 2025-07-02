import os, logging
from variables import Variables, StaticVariables

def setup_logger():
    fmt = "[{asctime}] [{levelname}] [{module}.{funcName}:{lineno}]: {message}"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        filename=os.path.join(StaticVariables.logs_path, Variables.session_id + ".log"),
        encoding="utf-8",
        filemode="a",
        level=logging.NOTSET,
        format=fmt, datefmt=datefmt, style="{"
    )
    logger = logging.getLogger()

    # setup console logging #
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt, style="{"))
    logger.addHandler(console_handler)

    # loaded #
    logger.debug("Logger loaded!")