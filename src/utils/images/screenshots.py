import logging
import platform
import numpy as np

from utils.logs import disable_spammy_loggers
from config import Config
current_os = platform.system()

# load bettercam #
if current_os == "Windows" and Config.SCREENSHOT_PACKAGE == "bettercam":
    try:
        import bettercam

        camera = bettercam.create(output_idx=0, output_color="BGRA")
        disable_spammy_loggers()

        def take_screenshot(region, sct):
            image = None
            try:
                image = camera.grab(region=(
                    region["left"],
                    region["top"],
                    region["left"] + region["width"],
                    region["top"] + region["height"]
                ))
            except Exception as e:
                logging.error(f"Failed to take screenshot (using mss as fallback): {e}")

            if image is None: image = np.array(sct.grab(region), dtype=np.uint8)
            return image

        def screenshot_cleanup():
            logging.info("Cleaning...")
            camera.release()

        logging.info("Screenshot package: bettercam")
    except Exception as e:
        logging.error(f"Failed to initialize bettercam: {e}")
        logging.info("\n\nScreenshot package: mss")

        def take_screenshot(region, sct):
            return np.array(sct.grab(region), dtype=np.uint8)

        def screenshot_cleanup(): pass

else: 
    logging.info("Screenshot package: mss")
    def take_screenshot(region, sct):
        return np.array(sct.grab(region), dtype=np.uint8)

    def screenshot_cleanup(): pass
