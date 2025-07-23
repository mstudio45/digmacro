import platform

# import logging
# from config import Config

__all__ = ["take_screenshot", "screenshot_cleanup"]
# current_os = platform.system()
# if current_os == "Windows" and Config.SCREENSHOT_PACKAGE == "bettercam":
#     logging.info("Screenshot package: bettercam")
# 
#     import bettercam # type: ignore
#     camera = bettercam.create(output_idx=0, output_color="BGRA")
# 
#     from utils.logs import disable_spammy_loggers
#     disable_spammy_loggers()
#     
#     def take_screenshot(region, sct=None):
#         try:
#             return camera.grab(region=(
#                 region["left"],
#                 region["top"],
#                 region["left"] + region["width"],
#                 region["top"] + region["height"]
#             ))
#         except Exception as e:
#             logging.error(f"Failed to take screenshot: {e}")
#             return None
# 
#     def screenshot_cleanup():
#         logging.info("Cleaning...")
#         camera.release()
# 
# else: # use mss if that if statement is false #
import numpy as np

# import mss
from mss.base import MSSBase

def take_screenshot(region, sct: MSSBase):
    return np.array(sct.grab(region), dtype=np.uint8)

def screenshot_cleanup(): pass