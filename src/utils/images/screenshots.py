import logging
import platform
import numpy as np

from utils.logs import disable_spammy_loggers
from config import Config
current_os = platform.system()

# load mss first #
def take_screenshot(region, sct):
    return np.array(sct.grab(region), dtype=np.uint8)

def screenshot_cleanup(): pass

# load bettercam #
if current_os == "Windows" and Config.SCREENSHOT_PACKAGE == "bettercam":
    try:
        import bettercam

        camera = bettercam.create(output_idx=0, output_color="BGRA")
        disable_spammy_loggers()

        del take_screenshot, screenshot_cleanup  # remove mss functions #

        def take_screenshot(region, sct=None):
            try:
                return camera.grab(region=(
                    region["left"],
                    region["top"],
                    region["left"] + region["width"],
                    region["top"] + region["height"]
                ))
            except Exception as e:
                logging.error(f"Failed to take screenshot: {e}")
                return None

        def screenshot_cleanup():
            logging.info("Cleaning...")
            camera.release()

        logging.info("Screenshot package: bettercam")
    except Exception as e:
        logging.error(f"Failed to initialize bettercam: {e}")
        logging.info("\n\nScreenshot package: mss")
        
else: logging.info("Screenshot package: mss")