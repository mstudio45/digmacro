import time, threading
import pyautogui, cv2
import logging

# setup variables #
__all__ = ["focus_window", "WindowFocuser"]

def focus_window(window_name):
    wnd = pyautogui.getWindowsWithTitle(window_name)[0]
    if wnd is None: return False
    wnd.activate()
    return True

class WindowFocuser(threading.Thread):
    def __init__(self, window_name):
        super().__init__()
        self.window_name = window_name

        self._stop_event = threading.Event()
        self.daemon = True

    def run(self):
        while not self._stop_event.is_set():
            try: cv2.setWindowProperty(self.window_name, cv2.WND_PROP_TOPMOST, 1)
            except: pass
            time.sleep(0)
        
        logging.info("Stopped successfully.")

    def stop(self):
        self._stop_event.set()