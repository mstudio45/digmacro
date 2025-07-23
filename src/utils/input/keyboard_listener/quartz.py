import time, logging, re, threading
from typing import Callable

from variables import Variables
from utils.input.key_converter.darwin import KeyConverter

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

__all__ = ["setup_global_hotkeys"]

MODIFIER_FLAGS = {
    'ctrl': Quartz.kCGEventFlagMaskControl,
    'shift': Quartz.kCGEventFlagMaskShift,
    'alt': Quartz.kCGEventFlagMaskAlternate,
    'cmd': Quartz.kCGEventFlagMaskCommand
}

key_converter = KeyConverter()

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