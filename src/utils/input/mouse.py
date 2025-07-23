import time
import platform
import logging
from config import Config

__all__ = ["move_mouse", "left_click", "left_click_lock", "clicking_lock"]
current_os = platform.system()

# import correct handlers #
if current_os == "Darwin" and Config.MOUSE_INPUT_PACKAGE == "Quartz":
    logging.info(f"Mouse Input Package: Quartz")
    from .mouse_handler.quartz import move_mouse, left_click, left_click_lock, get_mouse_pos, clicking_lock

elif current_os == "Windows" and Config.MOUSE_INPUT_PACKAGE == "win32api":
    logging.info(f"Mouse Input Package: win32api")
    from .mouse_handler.win32api import move_mouse, left_click, left_click_lock, get_mouse_pos, clicking_lock

elif Config.MOUSE_INPUT_PACKAGE == "pynput":
    logging.info(f"Mouse Input Package: pynput")
    from .mouse_handler.pynput import move_mouse, left_click, left_click_lock, get_mouse_pos, clicking_lock