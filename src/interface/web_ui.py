import sys, time, threading, logging, traceback
import webbrowser
import webview, platform, subprocess

try: import cv2
except ImportError as e:
    if "numpy" in str(e):
        import numpy as np
        import cv2
    else: raise e

from config import Config
from utils.images.screen import image_to_base64
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
    def resize_window(self, width, height, device_pixel_ratio=None):
        if device_pixel_ratio is not None and current_os == "Windows":
            width, height = int(width * device_pixel_ratio), int(height * device_pixel_ratio)
            logging.info(f"Resizing window: ({width}, {height}) | Scale: {device_pixel_ratio}")
        
        else:
            width, height = int(width), int(height)
            logging.info(f"Resizing window: ({width}, {height})")

        self.window.resize(width, height)
        return "Done"

    def get_macro_information(self):
        return f"{Variables.session_id} | {Variables.current_version} ({Variables.current_branch})"
    
    def get_scale_override(self):
        return Config.UI_SCALE_OVERRIDE
    
    # window functions #
    def stop_window(self):
        if self.window: self.window.destroy()
        logging.info("[UIBase] Window destroyed successfully.")

    def create_window(self):
        logging.debug("Fetching 'UI_ON_TOP' configuration...")
        is_on_top = True
        if hasattr(Config, "UI_ON_TOP"):
            if isinstance(Config.UI_ON_TOP, bool):
                is_on_top = Config.UI_ON_TOP

        logging.debug(f"Creating a new pywebview window - on_top={is_on_top}...")
        self.window = webview.create_window(
            "mstudio45's DIG macro",
            html=self.html,
            
            width=672, height=101,

            frameless=True, easy_drag=False,
            transparent=False, shadow=True,
            on_top=is_on_top, focus=True
        )
        self.window.expose(self.resize_window, self.get_macro_information, self.get_scale_override)
        logging.debug("Window has been created.")

class WebUI(UIBase):
    def __init__(self, finder):
        super().__init__(StaticVariables.ui_filepath)

        self.finder = finder
        self.next_logic_thread = None
        self.open_config = False
        self.restart_macro = False

        self._stop_event = threading.Event() # for some reason that shows up on linux bin, so lets just add it
    
    # api functions #
    def open_link(self, url):
        global current_os

        try:
            if current_os == "Windows":
                webbrowser.open(url)
            else:
                subprocess.run([Variables.unix_open_app_cmd, url])
        except Exception as e: logging.error(f"Failed to open link: {e}")

    def close(self):
        logging.info("WebUI closing using 'close'...")
        try: self.window.evaluate_js('updateStatus("Closing", "Please wait...", "red")')
        except: pass

        Variables.is_running = False
        if self.next_logic_thread: self.next_logic_thread.join()
        self.stop_window()

    def go_to_config(self):
        self.open_config = True
        self.close()

    def restart(self):
        self.restart_macro = True
        self.close()

    def pause(self):
        setattr(Variables, "is_paused", not Variables.is_paused)

        if Variables.is_paused:
            self.window.evaluate_js('updateStatus("Paused", "Resume to continue...", "gray")')
            self.window.evaluate_js('document.querySelector("#pausebtn").textContent = "Resume"')
        else:
            self.window.evaluate_js('updateStatus("Idle", "Waiting for minigame...", "yellow")')
            self.window.evaluate_js('document.querySelector("#pausebtn").textContent = "Pause"')

    # main handler #
    def start(self, next_logic=None):
        self.create_window()
        self.window.expose(self.close, self.go_to_config, self.restart, self.pause, self.open_link)

        # threads #
        threading.Thread(target=self.update, daemon=True).start()

        if next_logic:
            self.next_logic_thread = threading.Thread(target=next_logic, args=(self.window,), daemon=True)
            self.next_logic_thread.start()

        # start ui #
        logging.info("Starting Web UI (webview.start)...")
        webview.start(gui=gui_type)

    def update(self):
        if not Config.SHOW_COMPUTER_VISION:
            self.window.evaluate_js("removeComputerVision()")
            while not self._stop_event.is_set():
                self.window.evaluate_js(f'updateFps("{self.finder.current_fps:.2f}")')
                time.sleep(0.01)
        else:
            if Config.SHOW_DEBUG_MASKS: self.window.evaluate_js("changeImageSize(10)")
            if Config.FINDER_MULTITHREAD == True: self.window.evaluate_js("ignoreFps()")

            frame_time = 1 / Config.DEBUG_IMAGE_FPS
            while not self._stop_event.is_set():
                frame_start = time.perf_counter()
                
                try:
                    if self.finder.debug_img is not None and Variables.is_paused == False:
                        self.window.evaluate_js(f'updateImage("{image_to_base64(self.finder.debug_img)}", "{self.finder.current_fps:.2f}")')
                    else:
                        self.window.evaluate_js("clearImage()")
                except: pass
                
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

    def get_image(self):
        example_img = cv2.imread(StaticVariables.region_example_imgpath)
        base_64 = image_to_base64(example_img)
        return base_64

    # main handler #
    def start(self):
        self.create_window()
        self.window.expose(self.start_region_select, self.close, self.get_image)

        # start ui #
        logging.info("Starting Guide UI (webview.start)...")
        webview.start(gui=gui_type)

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
        logging.info("Starting Region UI (webview.start)...")
        webview.start(self.update, gui=gui_type)

    def update(self):
        logging.info("Loading buttons...")
        if "--region-check" not in sys.argv: 
            self.window.evaluate_js("updateStatus('Region Select', 'Please verify if the region detects everything correctly...', 'yellow')")
            self.window.evaluate_js("showRegionSelectButtons()")
        else:
            self.window.evaluate_js("updateStatus('Checking...', 'Waiting for exit...', 'green')")

        if Config.SHOW_DEBUG_MASKS: self.window.evaluate_js("changeImageSize(10)")

        while self.is_running == True:
            try:
                if self.finder.debug_img is not None:
                    self.window.evaluate_js(f'updateImage("{image_to_base64(self.finder.debug_img)}", "{self.finder.current_fps:.2f}")')
                else:
                    self.window.evaluate_js("clearImage()")
            except Exception as e: print(traceback.format_exc())
            time.sleep(0)