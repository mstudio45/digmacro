from config import Config
import logging, platform

current_os = platform.system()
__all__ = ["take_screenshot", "cleanup"]

if current_os == "Windows" and Config.SCREENSHOT_PACKAGE == "bettercam (Windows)":
    import bettercam # type: ignore
    camera = bettercam.create(output_idx=0, output_color="BGRA")

    # disable console spam #
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    for logger in loggers: 
        if logger.name.startswith("comtypes"): logger.setLevel(logging.CRITICAL)
    
    def take_screenshot(region, sct):
        return camera.grab(region=(
            region["left"],
            region["top"],
            region["left"] + region["width"],
            region["top"] + region["height"]
        ))

    def screenshot_cleanup():
        logging.info("Cleaning...")
        camera.release()

else: # use mss if that if statement is false
    import numpy as np

    def take_screenshot(region, sct):
        return np.array(sct.grab(region), dtype=np.uint8)

    def screenshot_cleanup(): 
        pass