from pynput.keyboard import Key, KeyCode
import logging

__all__ = ["get_key"]
class KeyConverter:
    def __init__(self):
        self._cache = {}

    def _get_pynput_key(self, normalized_key):
        # get special key from enum #
        if hasattr(Key, normalized_key): return getattr(Key, normalized_key)
        
        # get from char #
        try: 
            return KeyCode.from_char(normalized_key)
        except (ValueError, AttributeError) as e:
            logging.warning(f"Invalid keycode/char key: {normalized_key}. Error: {e}")
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
        key = self._get_pynput_key(normalized_key)
        logging.info(f"Using key: '{raw_key_str}' -> '{key}'.")

        if key is not None: 
            self._cache[normalized_key] = key
        
        return key