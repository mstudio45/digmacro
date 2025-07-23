from config import Config
import logging, platform

current_os = platform.system()
__all__ = ["take_screenshot", "cleanup"]

if current_os == "Windows" and Config.SCREENSHOT_PACKAGE == "bettercam":
    logging.info("Using 'bettercam' to take screenshots...\n")

    import bettercam # type: ignore
    camera = bettercam.create(output_idx=0, output_color="BGRA")

    from utils.logs import disable_spammy_loggers
    disable_spammy_loggers()
    
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

else: # use mss if that if statement is false #
    logging.info("Using 'mss' to take screenshots...\n")
    import numpy as np

    def take_screenshot(region, sct):
        return np.array(sct.grab(region), dtype=np.uint8)

    def screenshot_cleanup(): 
        pass