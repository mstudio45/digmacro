import logging

# https://github.com/kenorb/kenorb/blob/master/scripts/python/Quartz/keyboard.py #
__all__ = ["KeyConverter"]

class KeyConverter:
    def __init__(self):
        self._cache = {}

        self._quartz_shift_required_map = { # key that we want = key that we need to press with shift #
            '~': '`',
            '!': '1',
            '@': '2',
            '#': '3',
            '$': '4',
            '%': '5',
            '^': '6',
            '&': '7',
            '*': '8',
            '(': '9',
            ')': '0',
            '_': '-',
            '+': '=',
            '{': '[',
            '}': ']',
            '|': '\\',
            ':': ';',
            '"': '\'',
            '<': ',',
            '>': '.',
            '?': '/'
        }

        self._quartz_keycode_map = {
            # function keys #
            'f1': 0x7A, 'f2': 0x78, 'f3': 0x63, 'f4': 0x76, 'f5': 0x60, 'f6': 0x61,
            'f7': 0x62, 'f8': 0x64, 'f9': 0x65, 'f10': 0x6D, 'f11': 0x67, 'f12': 0x6F,
            'f13': 0x69, 'f14': 0x6B, 'f15': 0x71, 'f16': 0x6A, 'f17': 0x40, 'f18': 0x4F,
            'f19': 0x50, 'f20': 0x5A,

            # special keys #
            'esc': 0x35,
            'backspace': 0x33,
            'tab': 0x30,
            'enter': 0x24,
            'space': 0x31,
            'delete': 0x75,
            'home': 0x73,
            'end': 0x77,
            'page_up': 0x74,
            'page_down': 0x79,
            'caps_lock': 0x39,

            # arrows #
            'left': 0x7B,
            'right': 0x7C,
            'up': 0x7E,
            'down': 0x7D,

            # modifiers #
            'shift': 0x38,
            'shift_l': 0x38,
            'shift_r': 0x3C,

            'ctrl': 0x3B,
            'ctrl_l': 0x3B,
            'ctrl_r': 0x3E,

            'alt': 0x3A,
            'alt_l': 0x3A,
            'alt_r': 0x3D,

            # numbers #
            '0': 0x1D, '1': 0x12, '2': 0x13, '3': 0x14, '4': 0x15,
            '5': 0x17, '6': 0x16, '7': 0x1A, '8': 0x1C, '9': 0x19,

            # letters #
            'a': 0x00, 'b': 0x0B, 'c': 0x08, 'd': 0x02, 'e': 0x0E, 'f': 0x03, 'g': 0x05,
            'h': 0x04, 'i': 0x22, 'j': 0x26, 'k': 0x28, 'l': 0x25, 'm': 0x2E, 'n': 0x2D,
            'o': 0x1F, 'p': 0x23, 'q': 0x0C, 'r': 0x0F, 's': 0x01, 't': 0x11, 'u': 0x20,
            'v': 0x09, 'w': 0x0D, 'x': 0x07, 'y': 0x10, 'z': 0x06,

            # symbols #
            '`': 0x32,
            '-': 0x1B,
            '=': 0x18,
            '[': 0x21,
            ']': 0x1E,
            '\\': 0x2A,
            ';': 0x29,
            "'": 0x27,
            ',': 0x2B,
            '.': 0x2F,
            '/': 0x2C,
        }

        # funcs #
        def _get_quartz_key(self, normalized_key):
            requires_shift = False
            quartz_key = None

            # convert to shift key #
            if normalized_key.isalpha() and not normalized_key.islower():
                requires_shift = True
                normalized_key = normalized_key.lower()
            
            if normalized_key in self._quartz_shift_required_map:
                requires_shift = True
                normalized_key = self._quartz_shift_required_map[normalized_key]
            
            # get key from map #
            if normalized_key in self._quartz_keycode_map:
                quartz_key = self._quartz_keycode_map[normalized_key]
            elif len(normalized_key) == 1:
                quartz_key = ord(normalized_key)
            else:
                quartz_key = None
            
            # info and return #
            if quartz_key is None: 
                logging.warning(f"Invalid Quartz key: {normalized_key}")
            
            return quartz_key, requires_shift

        # main function #
        def get_key(raw_key_str):
            # validate key #
            if not raw_key_str: return None # invalid #
            normalized_key = str(raw_key_str).lower().strip()

            # get the key from cache #
            key = self._cache.get(normalized_key, None)
            if key is not None:
                logging.info(f"Using cached key: '{raw_key_str}' -> '{key}'.")
                return key

            # get the key and store in cache #
            key = _get_quartz_key(normalized_key)
            logging.info(f"Using key: '{raw_key_str}' -> '{key}'.")
            
            if key is not None:
                self._cache[normalized_key] = key
                
            return key