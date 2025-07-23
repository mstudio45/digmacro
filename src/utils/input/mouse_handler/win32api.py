import time
import threading
import win32con, ctypes, autoit
from variables import Variables
from utils.input.mouse_handler.movement_handler import smooth_move_to

user32 = ctypes.windll.user32
full_left_click = (win32con.MOUSEEVENTF_LEFTDOWN) + (win32con.MOUSEEVENTF_LEFTDOWN << 1)
clicking_lock = threading.Lock()

# mouse info and movement #
def get_mouse_pos():
    return autoit.mouse_get_pos()

def _move_autoit(x: int, y: int) -> None:
    autoit.mouse_move(x, y, speed=0)

def move_mouse(x: int, y: int, steps: int = 13, delay: float = 0.001) -> None:
    if not Variables.is_running: return
    smooth_move_to(get_mouse_pos(), x, y, _move_autoit, steps, delay)

# left click #
def left_click_lock(click_delay = 0):
    if not Variables.is_running: return
    if click_delay > 0: time.sleep(click_delay)

    user32.mouse_event(full_left_click, 0, 0, 0, 0)
    clicking_lock.release()

def left_click():
    if not Variables.is_running: return
    user32.mouse_event(full_left_click, 0, 0, 0, 0)