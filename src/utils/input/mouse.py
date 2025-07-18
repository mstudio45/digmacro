import time, threading, platform
import pynput, logging

from config import Config
from variables import Variables

current_os = platform.system()
__all__ = [
    "clicking_lock", "_pynput_mouse_controller",
    "left_click", "left_click_lock",
    "right_down", "right_up",
    "move_mouse"
]

clicking_lock = threading.Lock() # using lock
_pynput_mouse_controller = pynput.mouse.Controller()

def smooth_move_to(start_pos, dest_x, dest_y, cursor_func, steps=13, delay=0.001):
    current_x, current_y = start_pos
    
    step_x = (dest_x - current_x) / steps
    step_y = (dest_y - current_y) / steps
    
    for i in range(1, steps + 1):
        new_x = int(current_x + (step_x * i))
        new_y = int(current_y + (step_y * i))
        
        cursor_func(new_x, new_y)
        time.sleep(delay)

if current_os == "Windows" and Config.MOUSE_INPUT_PACKAGE == "win32api": # (TO-DO: linux evdev)
    logging.info("Using 'win32api' mouse handler...")
    import win32con, ctypes, autoit # type: ignore

    # setup user32 #
    user32 = ctypes.windll.user32
    full_left_click = (win32con.MOUSEEVENTF_LEFTDOWN) + (win32con.MOUSEEVENTF_LEFTDOWN << 1)
    
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

    # mouse move #
    def _move_autoit(x, y): autoit.mouse_move(x, y, speed=0)
    def move_mouse(x, y, steps=13, delay=0.001): smooth_move_to(autoit.mouse_get_pos(), x, y, _move_autoit, steps, delay)
    
elif current_os == "Darwin" and Config.MOUSE_INPUT_PACKAGE == "Quartz":
    logging.info("Using 'Quartz' mouse handler...")
    from Quartz import * # type: ignore
    from AppKit import NSEvent # type: ignore

    # left click #
    def left_click():
        if not Variables.is_running: return
        
        event_source = CGEventSourceCreate(kCGEventSourceStateCombinedSessionState) # type: ignore
        current_event = CGEventCreate(None) # type: ignore
        mouse_pos = CGEventGetLocation(current_event) if current_event else CGPointMake(100, 100) # type: ignore
        
        mouse_down = CGEventCreateMouseEvent(event_source, kCGEventLeftMouseDown, mouse_pos, kCGMouseButtonLeft) # type: ignore
        mouse_up = CGEventCreateMouseEvent(event_source, kCGEventLeftMouseUp, mouse_pos, kCGMouseButtonLeft) # type: ignore
        
        CGEventPost(kCGHIDEventTap, mouse_down) # type: ignore
        CGEventPost(kCGHIDEventTap, mouse_up) # type: ignore
    
    def left_click_lock(click_delay=0):
        if not Variables.is_running: return
        if click_delay > 0: time.sleep(click_delay)
        
        left_click()
        clicking_lock.release()

    # right click #
    def right_down():
        if not Variables.is_running: return
        
        event_source = CGEventSourceCreate(kCGEventSourceStateCombinedSessionState) # type: ignore
        current_event = CGEventCreate(None) # type: ignore
        mouse_pos = CGEventGetLocation(current_event) if current_event else CGPointMake(100, 100) # type: ignore
        
        mouse_down = CGEventCreateMouseEvent(event_source, kCGEventRightMouseDown, mouse_pos, kCGMouseButtonLeft) # type: ignore
        CGEventPost(kCGHIDEventTap, mouse_down) # type: ignore

    def right_up():
        if not Variables.is_running: return

        event_source = CGEventSourceCreate(kCGEventSourceStateCombinedSessionState) # type: ignore
        current_event = CGEventCreate(None) # type: ignore
        mouse_pos = CGEventGetLocation(current_event) if current_event else CGPointMake(100, 100) # type: ignore
        
        mouse_up = CGEventCreateMouseEvent(event_source, kCGEventRightMouseUp, mouse_pos, kCGMouseButtonLeft) # type: ignore
        CGEventPost(kCGHIDEventTap, mouse_up) # type: ignore

    # mouse move #
    def _move_quartz(x, y):
        event_source = CGEventSourceCreate(kCGEventSourceStateCombinedSessionState) # type: ignore
        mouse_move = CGEventCreateMouseEvent(event_source, kCGEventMouseMoved, CGPointMake(x, y), kCGMouseButtonLeft) # type: ignore
        CGEventPost(kCGHIDEventTap, mouse_move) # type: ignore

    def move_mouse(x, y, steps=13, delay=0.001): 
        event = NSEvent.mouseLocation()
        smooth_move_to((int(event.x), int(event.y)), x, y, _move_quartz, steps, delay)

else: # defaults to pynput
    logging.info("Using 'pynput' mouse handler...")
    pynput_button = pynput.mouse.Button
    full_left_click = pynput_button.left

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

    # mouse move #
    if current_os == "Windows":
        import autoit
        logging.info("Forcing 'autoit' for mouse movement since its the only package that Roblox wants to detect.")

        def _move_autoit(x, y): autoit.mouse_move(x, y, speed=0)
        def move_mouse(x, y, steps=13, delay=0.001): smooth_move_to(autoit.mouse_get_pos(), x, y, _move_autoit, steps, delay)
    else:
        def _move_pynput(x, y): _pynput_mouse_controller.position = (x, y)
        def move_mouse(x, y, steps=13, delay=0.001): smooth_move_to(_pynput_mouse_controller.position, x, y, _move_pynput, steps, delay)