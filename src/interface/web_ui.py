import os, time, threading, logging, traceback
import cv2
import webview, platform, subprocess

from config import Config
from utils.images.screen import image_to_base64, scale_x, scale_y
from variables import StaticVariables, Variables

current_os = platform.system()
__all__ = ["WebUI", "GuideUI", "RegionCheckUI"]

gui_type = "gtk"

class UIBase:
    def __init__(self, ui_path):
        self.next_logic_thread = None
        self.window = None
        self.html = open(ui_path, "r", encoding="utf-8").read()
    
    # api functions #
    def resize_window(self, width, height):
        if current_os == "Windows":
            width, height = int(width * scale_x), int(height * scale_y)
        else:
            width, height = int(width), int(height)
            
        self.window.resize(width, height)
        return "Done"

    def get_session_id(self):
        return Variables.session_id
    
    # window functions #
    def stop_window(self):
        if self.window: self.window.destroy()
        logging.info("[UIBase] Window destroyed successfully.")

    def create_window(self):
        self.window = webview.create_window(
            "mstudio45's DIG macro",
            html=self.html,
            
            width=672, height=101,

            frameless=True, easy_drag=False,
            transparent=False, shadow=True,
            on_top=True, focus=True
        )
        self.window.expose(self.resize_window, self.get_session_id)

class WebUI(UIBase):
    def __init__(self, finder):
        super().__init__(StaticVariables.ui_filepath)

        self.finder = finder
        self.next_logic_thread = None
        self._stop_event = threading.Event() # for some reason that shows up on linux bin, so lets just add it
    
    # api functions #
    def open_link(self, url):
        global current_os

        try:
            if current_os == "Windows":
                os.startfile(url)
            else:
                subprocess.run([Variables.unix_macos_open_cmd, url])
        except Exception as e: logging.error(f"Failed to open link: {e}")

    def close(self):
        logging.info("WebUI closing using 'close'...")
        try: self.window.evaluate_js('updateStatus("Closing", "Please wait...", "red")')
        except: pass

        Variables.is_running = False
        if self.next_logic_thread: self.next_logic_thread.join()
        self.stop_window()

    # main handler #
    def start(self, next_logic=None):
        self.create_window()
        self.window.expose(self.close, self.open_link)

        # threads #
        threading.Thread(target=self.update, daemon=True).start()

        if next_logic:
            self.next_logic_thread = threading.Thread(target=next_logic, args=(self.window,), daemon=True)
            self.next_logic_thread.start()

        # start ui #
        webview.start(gui=gui_type)

    def update(self):
        frame_time = 1 / Config.DEBUG_FPS

        while not self._stop_event.is_set():
            frame_start = time.perf_counter()
            
            try:
                if self.finder.debug_img is not None:
                    self.window.evaluate_js(f'updateImage("{image_to_base64(self.finder.debug_img)}")')
                else:
                    self.window.evaluate_js("clearImage()")
            except Exception as e: pass
            
            elapsed = time.perf_counter() - frame_start
            sleep_time = max(0, frame_time - elapsed)
            
            if sleep_time > 0: time.sleep(sleep_time)
        
        self.close()

class GuideUI(UIBase):
    def __init__(self):
        super().__init__(StaticVariables.guide_ui_filepath)
        self.is_running = True

    # api functions #
    def close(self):
        logging.info("GuideUI closing using 'close'...")

        self.is_running = False
        self.stop_window()

    def start_region_select(self):
        logging.info("GuideUI closing using 'start_region_select'...")
        self.stop_window()

    # main handler #
    def start(self):
        self.create_window()
        self.window.expose(self.start_region_select, self.close)

        # start ui #
        webview.start(self.update, gui=gui_type)

    def update(self):
        logging.info("Loading guide image...")

        example_img = cv2.imread(StaticVariables.region_example_imgpath)
        self.window.evaluate_js(f'updateImage("{image_to_base64(example_img)}")')

class RegionCheckUI(UIBase):
    def __init__(self, finder):
        super().__init__(StaticVariables.ui_filepath)

        self.finder = finder
        self.is_running = True
        self.is_okay = False
        self.restart_macro = False

    # api functions #
    def region_okay(self):
        logging.info("RegionCheckUI closing using 'region_okay'...")

        self.is_okay = True
        self.is_running = False
        self.stop_window()

    def close(self):
        logging.info("RegionCheckUI closing using 'close'...")

        self.is_running = False
        self.stop_window()

    def restart(self):
        logging.info("RegionCheckUI closing using 'restart'...")

        self.restart_macro = True
        self.stop_window()

    # main handler #
    def start(self):
        self.create_window()
        self.window.expose(self.region_okay, self.close, self.restart)

        # start ui #
        webview.start(self.update, gui=gui_type)

    def update(self):
        logging.info("Loading buttons...")
        self.window.evaluate_js("updateStatus('Region Select', 'Please verify if the region detects everything correctly...', 'yellow')")
        self.window.evaluate_js("showRegionSelectButtons()")

        while self.is_running == True:
            try:
                if self.finder.debug_img is not None:
                    self.window.evaluate_js(f'updateImage("{image_to_base64(self.finder.debug_img)}")')
                else:
                    self.window.evaluate_js("clearImage()")
            except Exception as e: print(traceback.format_exc())
            time.sleep(0)