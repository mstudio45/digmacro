import time, platform, traceback
import pynput, logging
from typing import Callable

# file imports #
from variables import Variables
from config import Config

__all__ = ["key_converter", "press_key", "press_multiple_keys"]

# setup keys #
from pynput.keyboard import Key, KeyCode
current_os = platform.system()

class KeyConverter:
    def __init__(self):
        self._cache = {}

        self.windows_vk_map = {
            # functions #
            'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74, 'f6': 0x75,
            'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
            'f13': 0x7C, 'f14': 0x7D, 'f15': 0x7E, 'f16': 0x7F, 'f17': 0x80, 'f18': 0x81,
            'f19': 0x82, 'f20': 0x83,

            # special keys #
            'esc': 0x1B,
            'backspace': 0x08,
            'tab': 0x09,
            'enter': 0x0D,
            'space': 0x20,
            'delete': 0x2E,
            'home': 0x24,
            'end': 0x23,
            'page_up': 0x21,
            'page_down': 0x22,
            'caps_lock': 0x14,

            # arrows #
            'left': 0x25,
            'right': 0x27,
            'up': 0x26,
            'down': 0x28,

            # modifiers #
            'shift': 0x10,
            'shift_l': 0xA0,
            'shift_r': 0xA1,

            'ctrl': 0x11,
            'ctrl_l': 0xA2,
            'ctrl_r': 0xA3,

            'alt': 0x12,
            'alt_l': 0xA4,
            'alt_r': 0xA5,

            # numbers #
            '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
            '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,

            # letters #
            'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46, 'g': 0x47,
            'h': 0x48, 'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E,
            'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54, 'u': 0x55,
            'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,

            # symbols #
            '`': 0xC0,
            '-': 0xBD,
            '=': 0xBB,
            '[': 0xDB,
            ']': 0xDD,
            '\\': 0xDC,
            ';': 0xBA,
            "'": 0xDE,
            ',': 0xBC,
            '.': 0xBE,
            '/': 0xBF,
        }

        self.quartz_keycode_map = {
            # functions #
            'f1': 122, 'f2': 120, 'f3': 99, 'f4': 118, 'f5': 96, 'f6': 97,
            'f7': 98, 'f8': 100, 'f9': 101, 'f10': 109, 'f11': 103, 'f12': 111,
            'f13': 105, 'f14': 107, 'f15': 113, 'f16': 106, 'f17': 64, 'f18': 79,
            'f19': 80, 'f20': 90,

            # special keys #
            'esc': 53,
            'backspace': 51,
            'tab': 48,
            'enter': 36,
            'space': 49,
            'delete': 117,
            'home': 115,
            'end': 119,
            'page_up': 116,
            'page_down': 121,
            'caps_lock': 272,

            # arrows #
            'left': 123,
            'right': 124,
            'up': 126,
            'down': 125,

            # modifiers #
            'shift': 257,
            'shift_l': 257,
            'shift_r': 258,

            'ctrl': 256,
            'ctrl_l': 256,
            'ctrl_r': 269,

            'alt': 261,
            'alt_l': 261,
            'alt_r': 262,

            'cmd': 259,
            'cmd_l': 259,
            'cmd_r': 260,

            'fn': 279,

            # numbers #
            '0': 29, '1': 18, '2': 19, '3': 20, '4': 21,
            '5': 23, '6': 22, '7': 26, '8': 28, '9': 25,

            # letters #
            'a': 0, 'b': 11, 'c': 8, 'd': 2, 'e': 14, 'f': 3, 'g': 5,
            'h': 4, 'i': 34, 'j': 38, 'k': 40, 'l': 37, 'm': 46, 'n': 45,
            'o': 31, 'p': 35, 'q': 12, 'r': 15, 's': 1, 't': 17, 'u': 32,
            'v': 9, 'w': 13, 'x': 7, 'y': 16, 'z': 6,

            # symbols #
            '`': 50,
            '-': 27,
            '=': 24,
            '[': 33,
            ']': 30,
            '\\': 42,
            ';': 41,
            "'": 39,
            ',': 43,
            '.': 47,
            '/': 44,
        }

    # funcs #
    def _normalize_key_string(self, key_str):
        return str(key_str).lower().strip()
    
    def _get_pynput_key(self, normalized_key):
        # get special key from enum #
        if hasattr(Key, normalized_key): return getattr(Key, normalized_key)
        
        # get from char #
        try: 
            return KeyCode.from_char(normalized_key)
        except (ValueError, AttributeError) as e:
            logging.warning(f"Invalid keycode/char key: {normalized_key}. Error: {e}")
            return None
    
    def _get_vk_key(self, normalized_key):
        # get special key from enum #
        if hasattr(Key, normalized_key): return getattr(Key, normalized_key)
        
        # get from vk #
        try:
            vk_key = self.windows_vk_map.get(normalized_key)
            return KeyCode.from_vk(vk_key)
        except Exception as e:
            logging.warning(f"Invalid VK Code key: {normalized_key}: {traceback.format_exc()}")
            return None

    def _get_quartz_key(self, normalized_key):
        quartz_key = self.quartz_keycode_map.get(normalized_key)
        if quartz_key is None: logging.warning(f"Invalid Quartz key: {normalized_key}")

        return quartz_key
    
    # main function #
    def get_key(self, key_str):
        if not key_str: return None # invalid #
        normalized_key = self._normalize_key_string(key_str)
        if normalized_key in self._cache: return self._cache[normalized_key]
        
        # get the key #
        key = None
        if current_os == "Darwin":
            key = self._get_quartz_key(normalized_key)
        elif current_os == "Windows":
            key = self._get_vk_key(normalized_key)
        else:
            key = self._get_pynput_key(normalized_key)

        # store to cache and return #
        if key is not None: self._cache[normalized_key] = key
        logging.info(f"Converted {key_str} to {key}.")

        return key

key_converter = KeyConverter()

# SETUP KEY LISTENER #
if current_os == "Darwin":
    logging.info("Using 'Quartz' for keyboard monitoring...")

    import logging, re, threading
    import Quartz # type: ignore
    from Quartz import ( # type: ignore
        CGEventTapCreate, CGEventTapEnable, CGEventGetFlags,
        CGEventGetIntegerValueField,

        CFMachPortCreateRunLoopSource, CFRunLoopAddSource, CFRunLoopGetCurrent,
        CFRunLoopRun, CFRunLoopStop, CFRunLoopTimerCreate, CFRunLoopAddTimer, 
        CFAbsoluteTimeGetCurrent, 
        
        kCGSessionEventTap, kCGHeadInsertEventTap, kCFRunLoopCommonModes,
        kCGEventKeyDown, kCGEventTapOptionDefault, kCGKeyboardEventKeycode,
        kCGEventTapDisabledByTimeout, kCGEventTapDisabledByUserInput
    )

    MODIFIER_FLAGS = {
        'ctrl': Quartz.kCGEventFlagMaskControl,
        'shift': Quartz.kCGEventFlagMaskShift,
        'alt': Quartz.kCGEventFlagMaskAlternate,
        'cmd': Quartz.kCGEventFlagMaskCommand
    }
    
    # key listener #
    def parse_hotkey(hotkey_str):
        mods = 0
        keys = re.findall(r'<(.*?)>', hotkey_str.lower())
        key = re.sub(r'<.*?>\+?', '', hotkey_str).lower()

        for mod in keys:
            mods |= MODIFIER_FLAGS.get(mod, 0)

        keycode = key_converter.get_key(key)
        if keycode is None:
            logging.critical(f"Unsupported key: {key}")
            return 0, 47

        return mods, keycode
    
    class EventTapHotkeyManager:
        def __init__(self):
            self.hotkeys = {}
            
            self._event_tap = None
            self._runloop_thread = None
            self._runloop_ref = None

        def _tap_callback(self, proxy, type_, event, refcon):
            try:
                if type_ == kCGEventTapDisabledByTimeout or type_ == kCGEventTapDisabledByUserInput:
                    CGEventTapEnable(self._event_tap, True)
                    return event
                
                if type_ == kCGEventKeyDown:
                    flags = CGEventGetFlags(event)
                    keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)

                    for (mod_mask, key), callback in self.hotkeys.items():
                        if key == keycode and (flags & mod_mask) == mod_mask:
                            callback()
                            break
            except Exception as e:
                logging.exception(f"Error in hotkey listener: {str(e)}")

            return event

        def start(self, hotkey_map: dict[str, Callable]):
            for combo, callback in hotkey_map.items():
                mods, keycode = parse_hotkey(combo)
                self.hotkeys[(mods, keycode)] = callback

            self._event_tap = CGEventTapCreate(
                kCGSessionEventTap,
                kCGHeadInsertEventTap,
                kCGEventTapOptionDefault,
                Quartz.CGEventMaskBit(kCGEventKeyDown),
                self._tap_callback,
                None
            )

            if not self._event_tap:
                raise RuntimeError("Failed to create event tap. Input Monitoring permission is missing.")

            def run_loop():
                self._runloop_ref = CFRunLoopGetCurrent()
                runloop_source = CFMachPortCreateRunLoopSource(None, self._event_tap, 0)

                CFRunLoopAddSource(self._runloop_ref, runloop_source, kCFRunLoopCommonModes)
                CGEventTapEnable(self._event_tap, True)
                CFRunLoopRun()

            self._runloop_thread = threading.Thread(target=run_loop, daemon=True)
            self._runloop_thread.start()

            while self._runloop_ref is None or not Variables.is_running: time.sleep(0.1)

        def stop(self):
            if self._runloop_ref:
                def stop_callback(timer, info):
                    CFRunLoopStop(self._runloop_ref)

                timer = CFRunLoopTimerCreate(
                    None,
                    CFAbsoluteTimeGetCurrent(),
                    0, 0, 0,
                    stop_callback,
                    None
                )
                CFRunLoopAddTimer(self._runloop_ref, timer, kCFRunLoopCommonModes)

    def setup_global_hotkeys(hotkeys: dict[str, Callable]) -> EventTapHotkeyManager:
        manager = EventTapHotkeyManager()
        manager.start(hotkeys)
        return manager
    
else: # default to pynput key listener #
    logging.info("Using 'pynput' for keyboard monitoring...")

    # key listener #
    def setup_global_hotkeys(hotkeys: dict[str, Callable]) -> pynput.keyboard.GlobalHotKeys:
        manager = pynput.keyboard.GlobalHotKeys(hotkeys)
        manager.start()
        return manager

# SETUP KEYBOARD FUNCTIONS #
if current_os == "Darwin" and Config.KEYBOARD_INPUT_PACKAGE == "Quartz":
    logging.info("Using 'Quartz' keyboard handler...")

    # press/releae #
    def key_event(key_code, key_down):
        event = Quartz.CGEventCreateKeyboardEvent(None, key_code, key_down) # type: ignore
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event) # type: ignore

    def _press(key):   return key_event(key, True)
    def _release(key): return key_event(key, False)

else: # default to pynput
    logging.info("Using 'pynput' keyboard handler...")
    _pynput_keyboard_controller = pynput.keyboard.Controller()
    
    # press/release #
    def _press(key):   _pynput_keyboard_controller.press(key)
    def _release(key): _pynput_keyboard_controller.release(key)

# global funcs #
def press_key(raw_key, duration=0):
    if not Variables.is_running: return False
    
    # convert #
    key = key_converter.get_key(raw_key)
    if key is None:
        logging.error(f"Cannot convert invalid key: {raw_key}")
        return False

    # try to press #
    try:
        _press(key)
        if duration > 0: time.sleep(duration)
        _release(key)

        return True
    except Exception as e:
        logging.error(f"Failed to press key {raw_key}: {traceback.format_exc()}")
        return False

def press_multiple_keys(raw_keys, duration=0):
    if not Variables.is_running: return False
    
    # convert #
    keys = []
    for raw_key in raw_keys:
        key = key_converter.get_key(raw_key)
        if key is None:
            logging.error(f"Cannot convert invalid key: {raw_key}")
            return False
        keys.append(key)

    # try to press #
    try:
        for key in keys:            _press(key)
        if duration > 0: time.sleep(duration)
        for key in reversed(keys):  _release(key)

        return True
    except Exception as e:
        logging.error(f"Failed to press keys {raw_keys}: {traceback.format_exc()}")
        return False
    
logging.info("============ KEYBOARD MODULE LOADED ============")