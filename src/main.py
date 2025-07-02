# imports #
import os, sys, time, traceback
import subprocess, importlib

# install requirements #
if "__compiled__" in globals():
    print("File is compiled, skipping requirement installation.")
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

        # win32 api #
        "pywin32": "win32gui",

        # ui libs #
        "PyQt5": "PyQt5",

        # misc libs #
        "psutil": "psutil",
        "PyMsgBox": "pymsgbox",
        "logging": "logging",
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
total_idle_time = 0

if __name__ == "__main__":
    ## check version ##
    current_version = "2.0.0"
    current_branch = "dev"

    try:
        import requests, json
        req = requests.get("https://raw.githubusercontent.com/mstudio45/digmacro/refs/heads/storage/versions.json")
        versions = json.loads(req.text)

        # check versions #
        if current_branch not in versions: raise Exception(f"{current_branch} is not an valid branch.")
        if versions[current_branch] != current_version:
            pymsgbox.alert(f"A new version is avalaible at https://github.com/mstudio45/digmacro!\n{current_version} -> {versions[current_branch]}")
            os.startfile("https://github.com/mstudio45/digmacro")
        
        print(f"Running on v{current_version} -> Latest is v{versions[current_branch]} ")
    except Exception as e:
        pymsgbox.alert(f"Failed to check for new updates. {traceback.format_exc()}")

    print("Creating storage folder..."); FileHandler.create_folder("storage")
    Config.load_config()

    # create logs folder #
    if Config.LOGGING_ENABLED:
        FileHandler.create_folder(StaticVariables.logs_path)

    # import after config loaded #
    from utils.finder import MainHandler, SellUI
    from utils.pathfinding import PathfingingHandler
    from utils.general.input import left_click, press_key
    from utils.roblox import can_rejoin, rejoin_dig, is_roblox_focused
    from utils.logs import setup_logger; import logging

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
            setup_logger()

            if not os.path.isfile(StaticVariables.config_filepath):
                pymsgbox.alert("Seems like you are using this macro for the first time. If you need to change the config, run the 'edit.bat' file to open the GUI config editor.")

            # window update thread #
            debug_window_thread = DebugWindowThread()
            debug_window_thread.start()

            # setup bar position #
            finder.setup_bar()

            # create screenshot folders #
            if Config.PREDICTION_SCREENSHOTS:
                logging.info("Creating screenshot folders...")

                FileHandler.create_folder(StaticVariables.screenshots_path)
                FileHandler.create_folder(os.path.join(StaticVariables.screenshots_path, "/prediction"))
                FileHandler.create_folder(os.path.join(StaticVariables.screenshots_path, "prediction", Variables.session_id))

                StaticVariables.prediction_screenshots_path = os.path.join(StaticVariables.screenshots_path, "prediction", Variables.session_id)

            # functions #
            def sell_all_items(last_key=False):
                if Config.PATHFINDING == True and Config.AUTO_SELL_AFTER_PATHFINDING_MACRO == True:
                    if last_key:
                        logging.info("Selling items...")
                        sell_handler.sell_items(Variables.dig_count)
                    return

                not_sold = max(1, Variables.dig_count - sell_handler.total_sold)
                required = max(2, Config.AUTO_SELL_REQUIRED_ITEMS)
                can_sell = not_sold % required == 0

                if can_sell:
                    logging.info(f"Selling items... {not_sold} % {required}")
                    sell_handler.sell_items(Variables.dig_count)

            def start_minigame():
                if Variables.is_minigame_active: return
                logging.info("Starting minigame...")

                # start minigame #
                left_click()
                
                # waiting of max 1.5 sec #
                start = time.time()
                timed_out = False
                while Variables.running:
                    timed_out = (time.time() - start) > 1.5
                    if Variables.is_minigame_active == True or timed_out: break

                logging.debug(f"Timed out: {(time.time() - start) > 1.5} | Active: {Variables.is_minigame_active}")
                if timed_out and Variables.is_minigame_active == False:
                    logging.info("Equipping shovel...")
                    press_key("+") # equip the shovel #
                    time.sleep(0.15)

            # Player Bar Thread #
            def finder_thread_func():
                logging.info("Loop started.")

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
                    #     logging.debug(f"Performance: {fps:.1f} FPS | {avg_frame_time:.1f}ms/frame")
                    #     last_log_time = current_time
                    
                    if sleep_time > 0: time.sleep(sleep_time)

                logging.info("Stopped successfully.")

            def is_roblox_focused_thread_func():
                logging.info("Loop started.")

                while Variables.running:
                    Variables.roblox_focused = is_roblox_focused()
                    time.sleep(0.1)

                logging.info("Stopped successfully.")

            # threads #
            finder_thread = threading.Thread(target=finder_thread_func, daemon=True)
            finder_thread.start()

            is_roblox_focused_thread = threading.Thread(target=is_roblox_focused_thread_func, daemon=True)
            is_roblox_focused_thread.start()

            logging.info("------------ STARTED ---------------")
            while Variables.running:
                start = time.time()
                time.sleep(0.25)

                # keybinds #
                if keyboard.is_pressed("ctrl+e"): break

                # main handler #
                if Config.AUTO_REJOIN:
                    if can_rejoin(total_idle_time):
                        total_idle_time = 0
                        rejoin_dig()
                        continue

                    if Variables.is_rejoining: continue

                # skip main loop if roblox is not focused #
                if not Variables.roblox_focused: continue

                # handle idle_time, and skip if not in idle #
                if not Variables.is_idle():
                    total_idle_time = 0
                    continue
                total_idle_time = total_idle_time + 0.25
                
                # handling dig_count and if digging finished #
                digging_finished = False
                if Variables.last_minigame_interaction is not None and Variables.last_minigame_interaction != -1:
                    last_interact = int(Variables.last_minigame_interaction) / 1000

                    if last_interact > 0 and (time.time() - last_interact) >= 1.5:
                        Variables.dig_count = Variables.dig_count + 1
                        Variables.last_minigame_interaction = None

                        logging.debug("Added 1 to dig_count, waiting..."); 
                        digging_finished = True
                        time.sleep(0.75)
                else: digging_finished = True

                # skip if digging didnt finish #
                if not digging_finished: continue

                # pathfinding handler #
                was_last_key = False
                if Config.PATHFINDING == True:
                    was_last_key = pathfinding.start_walking()
                
                # auto sell #
                if Config.AUTO_SELL == True:
                    sell_all_items(last_key=was_last_key)

                # minigame handler #
                if Config.AUTO_START_MINIGAME == True:
                    start_minigame()
                
            #################################################################################################

            Variables.running = False
            logging.info("_____________________________________")
        
        except KeyboardInterrupt:
            logging.debug("Starting to stop...")

        except Exception as e:
            err_msg = f"Main loop error: \n{traceback.format_exc()}"
            logging.critical(err_msg)
            pymsgbox.alert(f"[CRITICAL ERROR] {err_msg}")
        
        finally:
            logging.info("------------ STOP ---------------")
            finder.cleanup() # clean win32api screenshot and other stuff #

            # clear screenshot folders (if empty) #
            if Config.PREDICTION_SCREENSHOTS:
                if FileHandler.is_folder_empty(StaticVariables.prediction_screenshots_path):
                    FileHandler.try_delete_folder(StaticVariables.prediction_screenshots_path)

            # stop threads #
            stop_thread("debug_window_thread", debug_window_thread)

            cv2.destroyAllWindows()
            logging.info("Stopped")