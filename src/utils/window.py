import time, threading
import win32gui, pyautogui, cv2

# setup variables #
__all__ = ["is_roblox_focused", "focus_window", "WindowFocuser"]

def is_roblox_focused():
    try:
        wnd = win32gui.GetForegroundWindow()
        if not wnd: return False
    
        title = win32gui.GetWindowText(wnd)
        return "roblox" == title.lower()
    except Exception as e:
        print(f"[is_roblox_focused] Error checking focus: {e}")
        return False

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
        
        print("[WindowFocuser] Stopped successfully.")

    def stop(self):
        self._stop_event.set()