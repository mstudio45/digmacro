import time, threading, platform
import pynput, logging

from config import Config
from variables import Variables

current_os = platform.system()
__all__ = ["left_click", "move_mouse", "clicking_lock"]

clicking_lock = threading.Lock() # using lock

if current_os == "Windows" and Config.MOUSE_INPUT_PACKAGE == "win32api": # (TO-DO: linux evdev)
    logging.info("Using 'win32api' mouse handler...")

    import win32con, ctypes, autoit # type: ignore

    # setup user32 #
    user32 = ctypes.windll.user32
    full_left_click = (win32con.MOUSEEVENTF_LEFTDOWN) + (win32con.MOUSEEVENTF_LEFTDOWN << 1)
    
    def left_click_lock(click_delay = 0):
        if not Variables.is_running: return
        if click_delay > 0: time.sleep(click_delay)
    
        user32.mouse_event(full_left_click, 0, 0, 0, 0)
        clicking_lock.release()

    def left_click():
        if not Variables.is_running: return
        user32.mouse_event(full_left_click, 0, 0, 0, 0)

    def move_mouse(x, y):
        if not Variables.is_running: return
        autoit.mouse_move(x, y)
    
elif current_os == "Darwin" and Config.MOUSE_INPUT_PACKAGE == "Quartz":
    logging.info("Using 'Quartz' mouse handler...")
    from Quartz import * # type: ignore

    def left_click_lock(click_delay=0):
        if not Variables.is_running: return
        if click_delay > 0: time.sleep(click_delay)
        
        event_source = CGEventSourceCreate(kCGEventSourceStateCombinedSessionState) # type: ignore
        current_event = CGEventCreate(None) # type: ignore
        mouse_pos = CGEventGetLocation(current_event) if current_event else CGPointMake(100, 100) # type: ignore
        
        mouse_down = CGEventCreateMouseEvent(event_source, kCGEventLeftMouseDown, mouse_pos, kCGMouseButtonLeft) # type: ignore
        mouse_up = CGEventCreateMouseEvent(event_source, kCGEventLeftMouseUp, mouse_pos, kCGMouseButtonLeft) # type: ignore
        
        CGEventPost(kCGHIDEventTap, mouse_down) # type: ignore
        CGEventPost(kCGHIDEventTap, mouse_up) # type: ignore
        
        clicking_lock.release()

    def left_click():
        if not Variables.is_running: return
        
        event_source = CGEventSourceCreate(kCGEventSourceStateCombinedSessionState) # type: ignore
        current_event = CGEventCreate(None) # type: ignore
        mouse_pos = CGEventGetLocation(current_event) if current_event else CGPointMake(100, 100) # type: ignore
        
        mouse_down = CGEventCreateMouseEvent(event_source, kCGEventLeftMouseDown, mouse_pos, kCGMouseButtonLeft) # type: ignore
        mouse_up = CGEventCreateMouseEvent(event_source, kCGEventLeftMouseUp, mouse_pos, kCGMouseButtonLeft) # type: ignore
        
        CGEventPost(kCGHIDEventTap, mouse_down) # type: ignore
        CGEventPost(kCGHIDEventTap, mouse_up) # type: ignore

    def move_mouse(x, y):
        if not Variables.is_running: return
        
        event_source = CGEventSourceCreate(kCGEventSourceStateCombinedSessionState) # type: ignore
        mouse_move = CGEventCreateMouseEvent(event_source, kCGEventMouseMoved, CGPointMake(x, y), kCGMouseButtonLeft) # type: ignore
        CGEventPost(kCGHIDEventTap, mouse_move) # type: ignore
    
else: # defaults to pynput
    logging.info("Using 'pynput' mouse handler...")
    _pynput_mouse_controller = pynput.mouse.Controller()

    full_left_click = pynput.mouse.Button.left
    def left_click_lock(click_delay=0):
        if click_delay > 0: time.sleep(click_delay)

        _pynput_mouse_controller.press(full_left_click)
        _pynput_mouse_controller.release(full_left_click)
        clicking_lock.release()

    def left_click():
        if not Variables.is_running: return
        _pynput_mouse_controller.press(full_left_click)
        _pynput_mouse_controller.release(full_left_click)

    def move_mouse(x, y):
        _pynput_mouse_controller.position = (x, y)