import time
import pynput
from variables import Variables

__all__ = ["press_key", "press_multiple_keys"]

# SETUP KEYBOARD #
_pynput_keyboard_controller = pynput.keyboard.Controller()

def press_key(key, duration = 0):
    if not Variables.is_running: return

    _pynput_keyboard_controller.press(key)
    if duration > 0: time.sleep(duration)
    _pynput_keyboard_controller.release(key)

def press_multiple_keys(keys, duration=0):
    if not Variables.is_running: return
    
    for key in keys: _pynput_keyboard_controller.press(key)
    if duration > 0: time.sleep(duration)
    for key in reversed(keys): _pynput_keyboard_controller.release(key)