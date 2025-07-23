import time
from Quartz import ( # type: ignore
    CGEventPost, CGEventCreateKeyboardEvent, kCGHIDEventTap,
    kCGEventKeyDown, kCGEventKeyUp
)

# press/releae #
def key_event(key_code, key_down):
    CGEventPost(kCGHIDEventTap, CGEventCreateKeyboardEvent(None, key_code, kCGEventKeyDown if key_down == True else kCGEventKeyUp)) # type: ignore

def press(quartz_key): 
    key, requires_shift = quartz_key

    if requires_shift:
        key_event(0x38, True) # shift key #
        time.sleep(0.01)

    key_event(key, True) # press the key #

    if requires_shift:
        time.sleep(0.01)
        key_event(0x38, False) # shift key #

def release(quartz_key):
    return key_event(quartz_key[0], False)