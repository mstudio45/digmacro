import time, threading
import pynput

from config import Config

__all__ = [
    "left_click", "press_key", "press_multiple_keys",
    "clicking_lock"
]

import platform; current_os = platform.system()

from variables import Variables

# SETUP MOUSE #
clicking_lock = threading.Lock() # using lock
if Config.MOUSE_INPUT_PACKAGE == "Native Calls" and current_os != "Linux": # Native Calls, only with Darwin and Windows (TO-DO: linux evdev)
    if current_os == "Windows": 
        import win32con, ctypes, pydirectinput # type: ignore

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
            try:
                pydirectinput.moveTo(x, y, duration=0.015)
                pydirectinput.move(1, 1, duration=0.01)
            except: pass
        
    elif current_os == "Darwin":
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
else:
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