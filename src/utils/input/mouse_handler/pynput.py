import time
import threading
import platform
import logging
from pynput.mouse import Controller, Button
from variables import Variables
from utils.input.mouse_handler.movement_handler import smooth_move_to

clicking_lock = threading.Lock()
current_os = platform.system()
mouse_controller = Controller()

# mouse info and movement #
if current_os == "Windows":
    logging.info("Using 'autoit' for mouse information and movement for Windows. Roblox doesn't detect mouse movement input from pynput.")
    import autoit  # type: ignore

    def get_mouse_pos():
        return autoit.mouse_get_pos()

    def _move_autoit(x: int, y: int) -> None:
        autoit.mouse_move(x, y, speed=0)

    def move_mouse(x: int, y: int, steps: int = 13, delay: float = 0.001) -> None:
        if not Variables.is_running: return
        smooth_move_to(get_mouse_pos(), x, y, _move_autoit, steps, delay)
else:
    def get_mouse_pos():
        return mouse_controller.position

    def _move_pynput(x: int, y: int) -> None:
        mouse_controller.position = (x, y)

    def move_mouse(x: int, y: int, steps: int = 13, delay: float = 0.001) -> None:
        if not Variables.is_running: return
        smooth_move_to(get_mouse_pos(), x, y, _move_pynput, steps, delay)
        time.sleep(0.01)

# left click #
def left_click_lock(click_delay: float = 0) -> None:
    if not Variables.is_running: return
    if click_delay > 0: time.sleep(click_delay)

    mouse_controller.press(button=Button.left)
    mouse_controller.release(button=Button.left)

    clicking_lock.release()

def left_click() -> None:
    if not Variables.is_running: return
    
    mouse_controller.press(button=Button.left)
    mouse_controller.release(button=Button.left)