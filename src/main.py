# imports #
import os, sys, time, traceback
import subprocess, importlib

# install requirements #
if "__compiled__" in globals():
    print("[main.py] File is compiled, skipping requirement installation.")
else:
    uninstall = {}
    required_packages = {
        # finder libs #
        "opencv-python": "cv2",
        "numpy": "numpy",
        "PyAutoGUI": "pyautogui",
        "mss": "mss",

        # input libs #
        "pynput": "pynput",
        "keyboard": "keyboard",

        "pydirectinput_rgx": "pydirectinput",
        "PyDirectInput": "pydirectinput",

        # updater libs #
        "requests": "requests",

        # misc libs #
        "PyMsgBox": "pymsgbox",

        # win32 api #
        "pywin32": "win32gui",

        # ui libs #
        "PyQt5": "PyQt5"
    }

    def check_packages():
        # uninstall #
        for pip_name, replace_pip_name in uninstall.items():
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", pip_name])
            except Exception as e:
                print(f"[check_packages] Failed to uninstall '{pip_name}' requirement to replace it with '{replace_pip_name}' requirement: \n{traceback.format_exc()}")
                sys.exit(1)

        reqs = subprocess.check_output([sys.executable, "-m", "pip", "freeze"])
        installed_packages = [r.decode().split('==')[0] for r in reqs.split()]
        missing_packages = []
        
        # check all packages #
        for pip_name, _package in required_packages.items():
            if pip_name not in installed_packages:
                missing_packages.append(pip_name)
        
        # check importerrors #
        for pip_name, package in required_packages.items():
            try: importlib.import_module(package)
            except ImportError: missing_packages.append(pip_name)

        if len(missing_packages) == 0:  return
        
        # install packages #
        for pip_name in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
            except Exception as e:
                print(f"[check_packages] Failed to install '{pip_name}' requirement: \n{traceback.format_exc()}")
                sys.exit(1)

    check_packages()

# set DPI #
try: import ctypes; ctypes.windll.shcore.SetProcessDpiAwareness(2)
except: pass

# imports #
import cv2, threading
import pyautogui, pydirectinput, keyboard
import pymsgbox
from PyQt5.QtWidgets import QApplication

# utils # 
from config import Config, ConfigUI
from variables import Variables, StaticVariables
  
import utils.general.filehandler as FileHandler
import utils.window as window_util
from utils.window import is_roblox_focused

# unslow packages #
pydirectinput.PAUSE = None
pydirectinput.MINIMUM_SLEEP_IDEAL = None
pydirectinput.MINIMUM_SLEEP_ACTUAL = None

pyautogui.PAUSE = 0
pyautogui.MINIMUM_DURATION = 0.0
pyautogui.MINIMUM_SLEEP = 0.0

# create threads #
def stop_thread(thread_name, thead):
    if thead is None:
        return 
    if thead.is_alive() == False:
        return
    
    thead.stop()
    thead.join(timeout=1)
    if thead.is_alive():
        print(f"[stop_thread] Warning: {thread_name} did not stop gracefully.")

class DebugWindowThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.window_focuser = window_util.WindowFocuser(Config.WINDOW_NAME)

        self._stop_event = threading.Event()
        self.daemon = True

    def run(self):
        global finder

        cv2.namedWindow(Config.WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
        time.sleep(0.01)
        self.window_focuser.start()

        while not self._stop_event.is_set():
            if cv2.getWindowProperty(Config.WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                Variables.running = False
                break
            
            if finder.debug_img is not None:
                cv2.imshow(Config.WINDOW_NAME, finder.debug_img)
            cv2.waitKey(10)

        stop_thread("window_focuser", self.window_focuser)
        print("[DebugWindowThread] Stopped successfully.")

    def stop(self):
        self._stop_event.set()
        stop_thread("window_focuser", self.window_focuser)

# variables for main loop #
retry_minigame_start = False

# functions #
def sell_all_items(sell_handler):
    if max(1, Variables.dig_count - sell_handler.total_sold) % max(2, Config.AUTO_SELL_REQUIRED_ITEMS) == 0:
        print(f"[main.py] Sell Anywhere: {Variables.dig_count - sell_handler.total_sold} % {Config.AUTO_SELL_REQUIRED_ITEMS}")
        sell_handler.sell_items(Variables.dig_count)

def start_minigame():
    if Variables.is_minigame_active: return
    print("[main.py] Starting minigame...")

    # start minigame #
    time.sleep(0.05)
    left_click()
    
    # waiting of max 1.5 sec #
    start = time.time()
    while Variables.running:
        if Variables.is_minigame_active == True or (time.time() - start) > 1.5: break

    print(f"[start_minigame] Timed out: {(time.time() - start) > 1.5} | Active: {Variables.is_minigame_active}")

if __name__ == "__main__":
    print("[main.py] Creating storage folder..."); FileHandler.create_folder("storage")
    Config.load_config()

    # import after config loaded #
    from utils.finder import MainHandler, SellUI
    from utils.pathfinding import PathfingingHandler
    from utils.general.input import left_click, press_key

    # create util classes #
    finder = MainHandler()
    pathfinding = PathfingingHandler()
    sell_handler = SellUI()

    if "--edit-config" in sys.argv:
        config_app = QApplication(sys.argv)
        config_ui = ConfigUI()
        config_ui.show()
        sys.exit(config_app.exec_())

    else:
        debug_window_thread = None
        
        try:
            Config.WINDOW_NAME = Config.WINDOW_NAME + " | " + Variables.session_id 

            if not os.path.isfile(StaticVariables.config_filepath):
                pymsgbox.alert("Seems like you are using this macro for the first time. If you need to change the config, run the 'edit.bat' file to open the GUI config editor.")

            # window update thread #
            debug_window_thread = DebugWindowThread()
            debug_window_thread.start()

            # setup bar position #
            finder.setup_bar()

            # create screenshot folders #
            if Config.PREDICTION_SCREENSHOTS:
                print("[main.py] Creating screenshot folders...")

                FileHandler.create_folder(StaticVariables.screenshots_path)
                FileHandler.create_folder(StaticVariables.screenshots_path + "/prediction")
                FileHandler.create_folder(StaticVariables.screenshots_path + f"/prediction/{Variables.session_id}")

                StaticVariables.prediction_screenshots_path = StaticVariables.screenshots_path + f"/prediction/{Variables.session_id}"

            # Player Bar Thread #
            def finder_thread_func():
                print("[finder_thread_func] Loop started.")

                custom_sct = None 
                if Config.SCREENSHOT_PACKAGE == "mss":
                    import mss
                    custom_sct = mss.mss()

                frame_time = 1 / Config.TARGET_FPS
                # performance_log_interval = 0.5
                # last_log_time = time.time()

                while Variables.running:
                    frame_start = time.perf_counter()
                    
                    # update state and click #
                    finder.update_state(custom_sct=custom_sct)
                    finder.handle_click()
                    
                    elapsed = time.perf_counter() - frame_start
                    sleep_time = max(0, frame_time - elapsed)
                    
                    # log perf (for debug) #
                    # current_time = time.time()
                    # if current_time - last_log_time >= performance_log_interval:
                    #     avg_frame_time = sum(finder.frame_times) / len(finder.frame_times) if finder.frame_times else 0
                    #     fps = 1000 / avg_frame_time if avg_frame_time > 0 else 0
                    #     print(f"Performance: {fps:.1f} FPS | {avg_frame_time:.1f}ms/frame")
                    #     last_log_time = current_time
                    
                    if sleep_time > 0: time.sleep(sleep_time)

                print("[finder_thread_func] Stopped successfully.")

            def is_roblox_focused_thread_func():
                print("[is_roblox_focused_thread] Loop started.")

                while Variables.running:
                    Variables.roblox_focused = is_roblox_focused()
                    time.sleep(0.1)

                print("[is_roblox_focused_thread] Stopped successfully.")

            # threads #
            finder_thread = threading.Thread(target=finder_thread_func, daemon=True)
            finder_thread.start()

            is_roblox_focused_thread = threading.Thread(target=is_roblox_focused_thread_func, daemon=True)
            is_roblox_focused_thread.start()

            print("------------ STARTED ---------------")
            while Variables.running:
                # keybinds #
                if keyboard.is_pressed("ctrl+e"): break
                
                # main handler #
                if not Variables.is_idle():
                    time.sleep(0.25)

                else: # idle #
                    if not Variables.roblox_focused:
                        time.sleep(0.25)
                        continue
    
                    # digging ended #
                    digging_finished = False
                    if Variables.last_minigame_interaction is not None and Variables.last_minigame_interaction != -1:
                        last_interact = int(Variables.last_minigame_interaction) / 1000

                        if last_interact > 0 and (time.time() - last_interact) >= 1.5:
                            Variables.dig_count = Variables.dig_count + 1
                            Variables.last_minigame_interaction = None

                            print(f"[main.py] Added 1 to dig_count, waiting...\n"); 
                            digging_finished = True
                            time.sleep(1.5)
                    else:
                        digging_finished = True

                    if digging_finished:
                        # auto sell #
                        if Config.AUTO_SELL == True:
                            sell_all_items(sell_handler=sell_handler)

                        # pathfinding handler #
                        if Config.PATHFINDING == True:
                            pathfinding.start_walking()

                        if Config.PATHFINDING == True or Config.AUTO_START_MINIGAME == True:
                            start_minigame()

                    time.sleep(0.1)

            Variables.running = False
            print("_____________________________________")
        
        except KeyboardInterrupt:
            print("Starting to stop...")

        except Exception as e:
            pymsgbox.alert(f"[main.py] Loading error: \n{traceback.format_exc()}")
        
        finally:
            print("------------ STOP ---------------")
            finder.cleanup() # clean win32api screenshot and other stuff #

            # clear screenshot folders (if empty) #
            if FileHandler.is_folder_empty(StaticVariables.prediction_screenshots_path):
                FileHandler.try_delete_folder(StaticVariables.prediction_screenshots_path)

            # stop threads #
            stop_thread("debug_window_thread", debug_window_thread)

            cv2.destroyAllWindows()
            print("Stopped")