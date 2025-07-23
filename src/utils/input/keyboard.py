import time
import logging
import platform
from config import Config

__all__ = ["press_key", "press_multiple_keys", "setup_global_hotkeys"]
current_os = platform.system()

# import correct handlers #
if current_os == "Darwin" and Config.KEYBOARD_INPUT_PACKAGE == "Quartz":
    logging.info(f"Keyboard Input Package: Quartz")
    from .key_converter.darwin import KeyConverter
    get_key = KeyConverter().get_key

    from .keyboard_handler.quartz import press, release
    from .keyboard_listener.quartz import setup_global_hotkeys

elif Config.KEYBOARD_INPUT_PACKAGE == "pynput":
    logging.info(f"Keyboard Input Package: pynput")
    if current_os == "Windows":
        from .key_converter.windows import KeyConverter
    elif current_os == "Linux":
        from .key_converter.linux import KeyConverter
    elif current_os == "Darwin":
        from .key_converter.darwin import KeyConverter
    get_key = KeyConverter().get_key

    from .keyboard_handler.pynput import press, release
    from .keyboard_listener.pynput import setup_global_hotkeys

# main functions #
def press_key(raw_key, duration=0):
    key = get_key(raw_key)
    if key is None: return False

    # press key #
    press(key)
    if duration > 0: time.sleep(duration)
    release(key)

def press_multiple_keys(raw_keys, duration=0):
    keys = [get_key(k) for k in raw_keys]
    if any(k is None for k in keys): return False

    # press keys #
    for k in keys: press(k)
    if duration > 0: time.sleep(duration)
    for k in reversed(keys): release(k)