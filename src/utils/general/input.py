import time, threading
import win32con, ctypes
import pydirectinput, pynput

__all__ = [
    "left_click", "press_key", "press_multiple_keys",
    "clicking_lock"
]

# SETUP MOUSE #
clicking_lock = threading.Lock() # using lock

# setup user32 #
user32 = ctypes.windll.user32
full_left_click = (win32con.MOUSEEVENTF_LEFTDOWN) + (win32con.MOUSEEVENTF_LEFTDOWN << 1)

def left_click(click_delay = 0):
    if click_delay > 0: time.sleep(click_delay)

    user32.mouse_event(full_left_click, 0, 0, 0, 0)
    if clicking_lock.locked(): clicking_lock.release()

def move_mouse(x, y):
    try:
        pydirectinput.moveTo(x, y, duration=0.015)
        pydirectinput.move(1, 1, duration=0.01)
    except: pass

# SETUP KEYBOARD #
_pynput_keyboard_controller = pynput.keyboard.Controller()

def press_key(key, duration = 0):
    _pynput_keyboard_controller.press(key)
    if duration > 0: time.sleep(duration)
    _pynput_keyboard_controller.release(key)

def press_multiple_keys(keys, duration=0):
    for key in keys: _pynput_keyboard_controller.press(key)
    if duration > 0: time.sleep(duration)
    for key in reversed(keys): _pynput_keyboard_controller.release(key)