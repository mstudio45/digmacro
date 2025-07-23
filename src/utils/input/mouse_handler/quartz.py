import time
import threading
from variables import Variables
from utils.input.mouse_handler.movement_handler import smooth_move_to

clicking_lock = threading.Lock()

# https://github.com/kenorb/kenorb/blob/master/scripts/python/Quartz/mouse.py #
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
    if not Variables.is_running: return
    smooth_move_to(get_mouse_pos(), x, y, _move_quartz, steps, delay)
    time.sleep(0.01)

# mouse click handlers #
def press_event(x, y, button=LEFT):
    event = CGEventCreateMouseEvent(None, down_key[button], CGPointMake(x, y), mouse[button])
    CGEventPost(kCGHIDEventTap, event)
    time.sleep(0.01)

def release_event(x, y, button=LEFT):
    event = CGEventCreateMouseEvent(None, up_key[button], CGPointMake(x, y), mouse[button])
    CGEventPost(kCGHIDEventTap, event)
    time.sleep(0.01)

# left click #
def left_click_lock(click_delay=0):
    if not Variables.is_running: return
    if click_delay > 0: time.sleep(click_delay)
    
    x, y = get_mouse_pos()
    press_event(x, y)
    release_event(x, y)

    clicking_lock.release()

def left_click():
    if not Variables.is_running: return

    x, y = get_mouse_pos()
    press_event(x, y)
    release_event(x, y)