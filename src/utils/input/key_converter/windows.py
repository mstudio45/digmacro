from pynput.keyboard import Key, KeyCode
import logging, traceback

__all__ = ["get_key"]
class KeyConverter:
    def __init__(self):
        self._cache = {}

        self._windows_vk_map = {
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
    
    def _get_vk_key(self, normalized_key):
        # get special key from enum #
        if hasattr(Key, normalized_key): return getattr(Key, normalized_key)
        
        # get from vk #
        try:
            vk_key = self._windows_vk_map.get(normalized_key)
            return KeyCode.from_vk(vk_key)
        except Exception as e:
            logging.warning(f"Invalid VK Code key: {normalized_key}: {traceback.format_exc()}")
            return None

    # main function #
    def get_key(self, raw_key_str):
        # validate key #
        if not raw_key_str: return None # invalid #
        normalized_key = str(raw_key_str).lower().strip()

        # get the key from cache #
        cached_key = self._cache.get(normalized_key, None)
        if cached_key is not None:
            logging.info(f"Using cached key: '{raw_key_str}' -> '{key}'.")
            return cached_key

        # get the key and store in cache #
        key = self._get_vk_key(normalized_key)
        logging.info(f"Using key: '{raw_key_str}' -> '{key}'.")

        if key is not None: 
            self._cache[normalized_key] = key
        
        return key