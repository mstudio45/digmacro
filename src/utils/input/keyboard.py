import time, platform
import pynput, logging
from variables import Variables
from typing import Callable

__all__ = ["press_key", "press_multiple_keys"]

# SETUP KEYBOARD #
current_os = platform.system()
_pynput_keyboard_controller = pynput.keyboard.Controller()

if current_os == "Darwin":
    logging.info("Using 'Darwin' keyboard handler...")

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

    def press_key(key, duration = 0):
        if not Variables.is_running: return

        _pynput_keyboard_controller.press(key)
        if duration > 0: time.sleep(duration)
        _pynput_keyboard_controller.release(key)

    def press_multiple_keys(keys, duration=0):
        if not Variables.is_running: return

        for key in keys:             _pynput_keyboard_controller.press(key)
        if duration > 0: time.sleep(duration)
        for key in reversed(keys):   _pynput_keyboard_controller.release(key)

    MODIFIER_FLAGS = {
        'ctrl': Quartz.kCGEventFlagMaskControl,
        'shift': Quartz.kCGEventFlagMaskShift,
        'alt': Quartz.kCGEventFlagMaskAlternate,
        'cmd': Quartz.kCGEventFlagMaskCommand
    }

    KEYCODE_MAP = {
        'a': 0,  's': 1,  'd': 2,  'f': 3,  'h': 4,  'g': 5,  'z': 6,  'x': 7,
        'c': 8,  'v': 9,  'b': 11, 'q': 12, 'w': 13, 'e': 14, 'r': 15, 'y': 16,
        't': 17, '1': 18, '2': 19, '3': 20, '4': 21, '6': 22, '5': 23, '=': 24,
        '9': 25, '7': 26, '-': 27, '8': 28, '0': 29, ']': 30, 'o': 31, 'u': 32,
        '[': 33, 'i': 34, 'p': 35, 'return': 36, 'l': 37, 'j': 38, "'": 39,
        'k': 40, ';': 41, '\\': 42, ',': 43, '/': 44, 'n': 45, 'm': 46, '.': 47,
        'space': 49
    }

    def parse_hotkey(hotkey_str):
        mods = 0
        keys = re.findall(r'<(.*?)>', hotkey_str.lower())
        key = re.sub(r'<.*?>\+?', '', hotkey_str).lower()

        for mod in keys:
            mods |= MODIFIER_FLAGS.get(mod, 0)

        keycode = KEYCODE_MAP.get(key)
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

elif current_os == "Windows":
    logging.info("Using 'Windows' keyboard handler...")

    from_vk = pynput.keyboard.KeyCode.from_vk
    VK_CODE = {
        "backspace": from_vk(0x08),
        "tab": from_vk(0x09),
        "clear": from_vk(0x0C),
        "enter": from_vk(0x0D),
        "shift": from_vk(0x10),
        "ctrl": from_vk(0x11),
        "alt": from_vk(0x12),
        "pause": from_vk(0x13),
        "caps_lock": from_vk(0x14),
        "esc": from_vk(0x1B),
        "spacebar": from_vk(0x20),
        "page_up": from_vk(0x21),
        "page_down": from_vk(0x22),
        "end": from_vk(0x23),
        "home": from_vk(0x24),
        "left_arrow": from_vk(0x25),
        "up_arrow": from_vk(0x26),
        "right_arrow": from_vk(0x27),
        "down_arrow": from_vk(0x28),
        "select": from_vk(0x29),
        "print": from_vk(0x2A),
        "execute": from_vk(0x2B),
        "print_screen": from_vk(0x2C),
        "ins": from_vk(0x2D),
        "del": from_vk(0x2E),
        "help": from_vk(0x2F),
        "0": from_vk(0x30),
        "1": from_vk(0x31),
        "2": from_vk(0x32),
        "3": from_vk(0x33),
        "4": from_vk(0x34),
        "5": from_vk(0x35),
        "6": from_vk(0x36),
        "7": from_vk(0x37),
        "8": from_vk(0x38),
        "9": from_vk(0x39),
        "a": from_vk(0x41),
        "b": from_vk(0x42),
        "c": from_vk(0x43),
        "d": from_vk(0x44),
        "e": from_vk(0x45),
        "f": from_vk(0x46),
        "g": from_vk(0x47),
        "h": from_vk(0x48),
        "i": from_vk(0x49),
        "j": from_vk(0x4A),
        "k": from_vk(0x4B),
        "l": from_vk(0x4C),
        "m": from_vk(0x4D),
        "n": from_vk(0x4E),
        "o": from_vk(0x4F),
        "p": from_vk(0x50),
        "q": from_vk(0x51),
        "r": from_vk(0x52),
        "s": from_vk(0x53),
        "t": from_vk(0x54),
        "u": from_vk(0x55),
        "v": from_vk(0x56),
        "w": from_vk(0x57),
        "x": from_vk(0x58),
        "y": from_vk(0x59),
        "z": from_vk(0x5A),
        "numpad_0": from_vk(0x60),
        "numpad_1": from_vk(0x61),
        "numpad_2": from_vk(0x62),
        "numpad_3": from_vk(0x63),
        "numpad_4": from_vk(0x64),
        "numpad_5": from_vk(0x65),
        "numpad_6": from_vk(0x66),
        "numpad_7": from_vk(0x67),
        "numpad_8": from_vk(0x68),
        "numpad_9": from_vk(0x69),
        "multiply_key": from_vk(0x6A),
        "add_key": from_vk(0x6B),
        "separator_key": from_vk(0x6C),
        "subtract_key": from_vk(0x6D),
        "decimal_key": from_vk(0x6E),
        "divide_key": from_vk(0x6F),
        "F1": from_vk(0x70),
        "F2": from_vk(0x71),
        "F3": from_vk(0x72),
        "F4": from_vk(0x73),
        "F5": from_vk(0x74),
        "F6": from_vk(0x75),
        "F7": from_vk(0x76),
        "F8": from_vk(0x77),
        "F9": from_vk(0x78),
        "F10": from_vk(0x79),
        "F11": from_vk(0x7A),
        "F12": from_vk(0x7B),
        "F13": from_vk(0x7C),
        "F14": from_vk(0x7D),
        "F15": from_vk(0x7E),
        "F16": from_vk(0x7F),
        "F17": from_vk(0x80),
        "F18": from_vk(0x81),
        "F19": from_vk(0x82),
        "F20": from_vk(0x83),
        "F21": from_vk(0x84),
        "F22": from_vk(0x85),
        "F23": from_vk(0x86),
        "F24": from_vk(0x87),
        "num_lock": from_vk(0x90),
        "scroll_lock": from_vk(0x91),
        "left_shift": from_vk(0xA0),
        "right_shift": from_vk(0xA1),
        "left_control": from_vk(0xA2),
        "right_control": from_vk(0xA3),
        "left_menu": from_vk(0xA4),
        "right_menu": from_vk(0xA5),
        "browser_back": from_vk(0xA6),
        "browser_forward": from_vk(0xA7),
        "browser_refresh": from_vk(0xA8),
        "browser_stop": from_vk(0xA9),
        "browser_search": from_vk(0xAA),
        "browser_favorites": from_vk(0xAB),
        "browser_start_and_home": from_vk(0xAC),
        "volume_mute": from_vk(0xAD),
        "volume_Down": from_vk(0xAE),
        "volume_up": from_vk(0xAF),
        "next_track": from_vk(0xB0),
        "previous_track": from_vk(0xB1),
        "stop_media": from_vk(0xB2),
        "play/pause_media": from_vk(0xB3),
        "start_mail": from_vk(0xB4),
        "select_media": from_vk(0xB5),
        "start_application_1": from_vk(0xB6),
        "start_application_2": from_vk(0xB7),
        "attn_key": from_vk(0xF6),
        "crsel_key": from_vk(0xF7),
        "exsel_key": from_vk(0xF8),
        "play_key": from_vk(0xFA),
        "zoom_key": from_vk(0xFB),
        "clear_key": from_vk(0xFE),
        "+": from_vk(0xBB),
        ",": from_vk(0xBC),
        "-": from_vk(0xBD),
        ".": from_vk(0xBE),
        "/": from_vk(0xBF),
        "`": from_vk(0xC0),
        ";": from_vk(0xBA),
        "[": from_vk(0xDB),
        "\\": from_vk(0xDC),
        "]": from_vk(0xDD),
        "'": from_vk(0xDE)
    }

    def press_key(key, duration = 0):
        if not Variables.is_running: return
        key = VK_CODE[key]

        _pynput_keyboard_controller.press(key)
        if duration > 0: time.sleep(duration)
        _pynput_keyboard_controller.release(key)

    def press_multiple_keys(keys, duration=0):
        if not Variables.is_running: return
        vk_keys = [VK_CODE[key] for key in keys]
        
        for key in vk_keys:             _pynput_keyboard_controller.press(key)
        if duration > 0: time.sleep(duration)
        for key in reversed(vk_keys):   _pynput_keyboard_controller.release(key)

    def setup_global_hotkeys(hotkeys: dict[str, Callable]) -> pynput.keyboard.GlobalHotKeys:
        manager = pynput.keyboard.GlobalHotKeys(hotkeys)
        manager.start()
        return manager
    
else:
    logging.info("Using 'General' keyboard handler...")

    def press_key(key, duration = 0):
        if not Variables.is_running: return

        _pynput_keyboard_controller.press(key)
        if duration > 0: time.sleep(duration)
        _pynput_keyboard_controller.release(key)

    def press_multiple_keys(keys, duration=0):
        if not Variables.is_running: return

        for key in keys:             _pynput_keyboard_controller.press(key)
        if duration > 0: time.sleep(duration)
        for key in reversed(keys):   _pynput_keyboard_controller.release(key)

    def setup_global_hotkeys(hotkeys: dict[str, Callable]) -> pynput.keyboard.GlobalHotKeys:
        manager = pynput.keyboard.GlobalHotKeys(hotkeys)
        manager.start()
        return manager  