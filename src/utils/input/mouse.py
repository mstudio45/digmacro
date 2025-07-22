import time, threading, platform
import pynput, logging

from config import Config
from variables import Variables

current_os = platform.system()
__all__ = [
    "clicking_lock", "_pynput_mouse_controller",
    "left_click", "left_click_lock",
    "right_down", "right_up",
    "move_mouse", "get_mouse_pos"
]

clicking_lock = threading.Lock() # using lock
_pynput_mouse_controller = pynput.mouse.Controller()

def smooth_move_to(start_pos, dest_x, dest_y, cursor_func, steps=13, delay=0.001):
    if steps == 1:
        return cursor_func(dest_x, dest_y)

    current_x, current_y = start_pos
    
    step_x = (dest_x - current_x) / steps
    step_y = (dest_y - current_y) / steps
    
    for i in range(1, steps + 1):
        new_x = int(current_x + (step_x * i))
        new_y = int(current_y + (step_y * i))
        
        cursor_func(new_x, new_y)
        time.sleep(delay)

# MOUSE HANDLER #
if current_os == "Windows" and Config.MOUSE_INPUT_PACKAGE == "win32api":
    logging.info("Using 'win32api' mouse handler...")
    import win32con, ctypes, autoit # type: ignore

    # setup user32 #
    user32 = ctypes.windll.user32
    full_left_click = (win32con.MOUSEEVENTF_LEFTDOWN) + (win32con.MOUSEEVENTF_LEFTDOWN << 1)
    
    # mouse pos #
    def get_mouse_pos(): return autoit.mouse_get_pos()

    # mouse move #
    def _move_autoit(x, y): autoit.mouse_move(x, y, speed=0)
    def move_mouse(x, y, steps=13, delay=0.001): smooth_move_to(get_mouse_pos(), x, y, _move_autoit, steps, delay)

    # left click #
    def left_click_lock(click_delay = 0):
        if not Variables.is_running: return
        if click_delay > 0: time.sleep(click_delay)
    
        user32.mouse_event(full_left_click, 0, 0, 0, 0)
        clicking_lock.release()

    def left_click():
        if not Variables.is_running: return
        user32.mouse_event(full_left_click, 0, 0, 0, 0)

    # right click #
    def right_down(): 
        if not Variables.is_running: return
        user32.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)

    def right_up():
        if not Variables.is_running: return
        user32.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    
elif current_os == "Darwin" and Config.MOUSE_INPUT_PACKAGE == "Quartz":
    # https://github.com/kenorb/kenorb/blob/master/scripts/python/Quartz/mouse.py #

    logging.info("Using 'Quartz' mouse handler...")
    from Quartz import (  # type: ignore
        CGEventCreate, CGEventCreateMouseEvent, CGEventGetLocation,
        CGPointMake, CGEventPost, CGEventSourceCreate,

        kCGHIDEventTap, kCGEventMouseMoved, kCGEventSourceStateCombinedSessionState,
        kCGEventLeftMouseDown, kCGEventRightMouseDown,
        kCGEventLeftMouseUp,   kCGEventRightMouseUp,
        kCGMouseButtonLeft,    kCGMouseButtonRight
    )

    down_key = [kCGEventLeftMouseDown, kCGEventRightMouseDown]
    up_key   = [kCGEventLeftMouseUp,   kCGEventRightMouseUp  ]
    mouse    = [kCGMouseButtonLeft,    kCGMouseButtonRight   ]
    [LEFT, RIGHT] = [0, 1]

    ## CGEventSourceCreate(kCGEventSourceStateCombinedSessionState) ##

    # mouse pos #
    def get_mouse_pos():
        event = CGEventGetLocation(CGEventCreate(None))
        return int(event.x), int(event.y)

    # mouse move #
    def _move_quartz(x, y):
        mouse_move = CGEventCreateMouseEvent(None, kCGEventMouseMoved, CGPointMake(x, y), kCGMouseButtonLeft)
        CGEventPost(kCGHIDEventTap, mouse_move)

    def move_mouse(x, y, steps=13, delay=0.001): 
        smooth_move_to(get_mouse_pos(), x, y, _move_quartz, steps, delay)
        time.sleep(0.01)

    # left click #
    def _press(x, y, button=LEFT):
        event = CGEventCreateMouseEvent(None, down_key[button], CGPointMake(x, y), mouse[button])
        CGEventPost(kCGHIDEventTap, event)
        time.sleep(0.01)

    def _release(x, y, button=LEFT):
        event = CGEventCreateMouseEvent(None, up_key[button], CGPointMake(x, y), mouse[button])
        CGEventPost(kCGHIDEventTap, event)
        time.sleep(0.01)

    def left_click():
        x, y = get_mouse_pos()
        _press(x, y)
        _release(x, y)

    def left_click_lock(click_delay=0):
        if click_delay > 0: time.sleep(click_delay)
        
        x, y = get_mouse_pos()
        _press(x, y)
        _release(x, y)

        clicking_lock.release()

    # right click #
    def right_down():
        x, y = get_mouse_pos()
        _press(x, y, button=RIGHT)

    def right_up():
        x, y = get_mouse_pos()
        _release(x, y, button=RIGHT)

else: # defaults to pynput
    logging.info("Using 'pynput' mouse handler...")
    pynput_button = pynput.mouse.Button
    full_left_click = pynput_button.left

    if current_os == "Windows":
        import autoit # type: ignore
        logging.info("Forcing 'autoit' for mouse movement since its the only package that Roblox wants to detect.")

        # mouse pos #
        def get_mouse_pos(): return autoit.mouse_get_pos()

        # mouse move #
        def _move_autoit(x, y): autoit.mouse_move(x, y, speed=0)
        def move_mouse(x, y, steps=13, delay=0.001): smooth_move_to(get_mouse_pos(), x, y, _move_autoit, steps, delay)
    else:
        # mouse pos #
        def get_mouse_pos(): return _pynput_mouse_controller.position

        # mouse move #
        def _move_pynput(x, y): _pynput_mouse_controller.position = (x, y)
        def move_mouse(x, y, steps=13, delay=0.001): 
            smooth_move_to(get_mouse_pos(), x, y, _move_pynput, steps, delay)
            time.sleep(0.01)

    # left click #
    def left_click_lock(click_delay=0):
        if click_delay > 0: time.sleep(click_delay)

        _pynput_mouse_controller.press(full_left_click)
        _pynput_mouse_controller.release(full_left_click)
        clicking_lock.release()

    def left_click():
        if not Variables.is_running: return
        _pynput_mouse_controller.press(full_left_click)
        _pynput_mouse_controller.release(full_left_click)

    # right click #
    def right_down():
        if not Variables.is_running: return
        _pynput_mouse_controller.press(pynput_button.right)

    def right_up():
        if not Variables.is_running: return
        _pynput_mouse_controller.release(pynput_button.right)

logging.info("============ MOUSE MODULE LOADED ============")