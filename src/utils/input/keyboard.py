import time
import logging
import platform
from config import Config

__all__ = ["press_key", "press_multiple_keys", "setup_global_hotkeys"]
current_os = platform.system()

# import correct handlers #
if current_os == "Darwin" and Config.KEYBOARD_INPUT_PACKAGE == "Quartz":
    from utils.input.key_converter.darwin import KeyConverter
    from utils.input.keyboard_listener.quartz import setup_global_hotkeys
    
    get_key = KeyConverter().get_key
    from utils.input.keyboard_handler.quartz import press, release

    logging.info(f"Keyboard Input Package: Quartz")
    logging.info(f"Keyboard Listener Package: Quartz")

elif Config.KEYBOARD_INPUT_PACKAGE == "pynput":
    if current_os == "Windows":
        from utils.input.key_converter.windows import KeyConverter
        from utils.input.keyboard_listener.pynput import setup_global_hotkeys

        logging.info(f"Keyboard Input Package: pynput")
        logging.info(f"Keyboard Listener Package: pynput")
        
    elif current_os == "Linux":
        from utils.input.key_converter.linux import KeyConverter
        from utils.input.keyboard_listener.pynput import setup_global_hotkeys
    
        logging.info(f"Keyboard Input Package: pynput")
        logging.info(f"Keyboard Listener Package: pynput")

    elif current_os == "Darwin":
        from utils.input.key_converter.darwin import KeyConverter
        from utils.input.keyboard_listener.quartz import setup_global_hotkeys

        logging.info(f"Keyboard Input Package: pynput")
        logging.info(f"Keyboard Listener Package: Quartz")
    
    get_key = KeyConverter().get_key
    from utils.input.keyboard_handler.pynput import press, release

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