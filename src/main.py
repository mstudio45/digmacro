# imports #
import os, sys, time, traceback, subprocess, platform

current_os = platform.system() # Linux, Windows, Darwin
if current_os not in ["Linux", "Darwin", "Windows"]:
    print(f"Current OS '{current_os}' is not supported.")
    sys.exit(0)

compiled = "__compiled__" in globals()
def restart_macro():
    if compiled:
        os.execvp(sys.argv[0], ["--skip-selection"])
    else:
        os.execvp(sys.executable, [sys.executable, os.path.abspath(__file__), "--skip-selection"])
    return

# install requirements #
from utils.packages.check_apt import check_apt_packages
from utils.packages.check_errors import check_special_errors
from utils.packages.check_python import check_pip_packages
from utils.packages.check_shutil import check_shutil_applications
from utils.packages.versions import check_package_version

if check_shutil_applications() or check_apt_packages() or check_pip_packages() or check_special_errors():
    if "--only-install" in sys.argv: os.kill(os.getpid(), 9)
    restart_macro()
    sys.exit(0)

if "--only-install" in sys.argv: os.kill(os.getpid(), 9)

# imports #
import logging, threading
import pyautogui, pynput, mss

from PySide6.QtWidgets import QApplication
import interface.msgbox as msgbox

# config and variables # 
from config import Config
from variables import Variables, StaticVariables

# utils #
import utils.general.filehandler as FileHandler

# unslow packages #
pyautogui.PAUSE = 0
pyautogui.MINIMUM_DURATION = 0.0
pyautogui.MINIMUM_SLEEP = 0.0

if __name__ == "__main__":
    # create folders #
    print("Creating storage folder...")
    FileHandler.create_folder("storage")

    print("Creating logs folder...")
    FileHandler.create_folder(StaticVariables.logs_path)

    print("Loading config...")
    Config.load_config() # default_config_loaded

    from utils.logs import setup_logger;
    print("Loading logger...")
    setup_logger()

    ## check version ##
    current_version = "2.0.1"
    current_branch = "beta"

    try:
        logging.info("Checking current version...")

        import requests, json
        req = requests.get("https://raw.githubusercontent.com/mstudio45/digmacro/refs/heads/storage/versions.json", timeout=2.5)
        versions = json.loads(req.text)

        # check versions #
        if current_branch not in versions: raise Exception(f"{current_branch} is not an valid branch.")
        if check_package_version(versions[current_branch], current_version):
            res = msgbox.confirm(f"A new version is avalaible at https://github.com/mstudio45/digmacro!\n{current_version} -> {versions[current_branch]}\nDo you want to open the Github repository?")
            if res == "Yes":
                try:
                    if current_os == "Windows":
                        os.startfile("https://github.com/mstudio45/digmacro")
                    else:
                        subprocess.run([Variables.unix_macos_open_cmd, "https://github.com/mstudio45/digmacro"])
                except Exception as e: logging.error(f"Failed to open link: {e}")
        
        logging.debug(f"Running on v{current_version} -> Latest is v{versions[current_branch]} ")
    except Exception as e:
        msgbox.alert(f"Failed to check for new updates. {traceback.format_exc()}", bypass=True)

    run_config = False

    if "--skip-selection" in sys.argv:
        logging.info("Skipping config/start selection.")
    else:
        res = msgbox.confirm("What would you like to do?", buttons=("Start Macro", "Edit the configuration", "Exit"))
        if res == "Edit the configuration":
            # config ui #
            logging.info("Loading Config GUI...")
            if current_os == "Linux":
                os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = ""
                os.environ["QT_STYLE_OVERRIDE"] = "fusion"

            from interface.config_ui import ConfigUI
            q_app = QApplication(sys.argv)
            config_ui = ConfigUI()
            config_ui.show()
            q_app.exec()

            if config_ui.start_macro_now == True:
                restart_macro()
            else: 
                os.kill(os.getpid(), 9)
        
        elif res == "Exit" or res == "": os.kill(os.getpid(), 9)
        else: logging.info("Starting the macro...")

    # main loader #
    logging.info("Importing libraries...")
    from utils.finder import MainHandler, SellUI
    from utils.pathfinding import PathfingingHandler

    from utils.general.mouse import left_click
    from utils.general.keyboard import press_key

    from utils.images.screenshots import screenshot_cleanup
    from utils.images.screen import screen_res_str

    from utils.roblox.rejoin import can_rejoin, rejoin_dig
    from utils.roblox.window import is_roblox_focused

    from utils.general.fps_counter import FPSCounter

    import interface.web_ui as WebUI
    from interface.region_selection import RegionSelector

    class MacroHandler:
        def __init__(self):
            # threads and functions #
            self.active_threads = []
            self.cleanup_functions = []

            # variables #
            self.saved_regions = {}

            self.total_idle_time = 0
            self.hotkeys = None

            # classes #
            self.region_selector = RegionSelector()
            self.finder = MainHandler()
            self.pathfinding = PathfingingHandler()
            self.sell_handler = SellUI()

            self.guide_ui = WebUI.GuideUI()
            self.region_check_ui = WebUI.RegionCheckUI(self.finder)
            self.ui = WebUI.WebUI(self.finder)

        # thread handler #
        def add_thread(self, name, thread):
            if thread in self.active_threads: return

            thread.name = name
            self.active_threads.append(thread)

        def stop_thread(self, thread, timeout=2):
            if thread in self.active_threads:
                self.active_threads.remove(thread)

            if thread.is_alive() == False: return True
            
            thread.stop()
            thread.join(timeout=timeout)
            if thread.is_alive(): 
                logging.warning(f"Warning: Thread '{thread.name or "???"}' did not stop gracefully.")
                return False
            
            return True

        # functions handler #
        def add_function(self, func):
            if func in self.cleanup_functions: return
            self.cleanup_functions.append(func)

        # region selector #
        def check_saved_region(self):
            logging.info("Checking saved region...")

            if Config.USE_SAVED_POSITION and os.path.isfile(StaticVariables.region_filepath):
                try:
                    pos = FileHandler.read(StaticVariables.region_filepath)
                    if pos is None: pass
                    self.saved_regions = json.loads(pos)

                    if screen_res_str in self.saved_regions:
                        region = self.saved_regions[screen_res_str]
                        if "left" in region and "top" in region and "width" in region and "height" in region:
                            logging.info(f"Using saved region '{screen_res_str}'.")
                            return region
                        else:
                            region = None
                except Exception as e:
                    msgbox.alert(f"Failed to load saved position: \n{traceback.format_exc()}", log_level=logging.ERROR)

            return None
        
        def setup_region_setter(self): # requires to be run in main thread #
            region = self.check_saved_region()
            if region == None:
                # load guide #
                logging.info("Showing guide...")

                self.guide_ui.start()
                if not Variables.is_running or self.guide_ui.is_running == False:
                    self.exit_macro()
                    return

                # start region select #
                logging.info("Starting region selection...")
                self.region_selector.start()
                region = self.region_selector.get_selection()
                if region == None:
                    self.exit_macro()
                    return

                logging.info("Region has been set.")
                Variables.minigame_region = region
                self.saved_regions[screen_res_str] = region

                # load region select checker ui #
                self.region_check_ui.start()
                if self.region_check_ui.restart_macro:
                    self.exit_macro()
                    restart_macro()
                    return
                
                if self.region_check_ui.is_okay == False:
                    self.exit_macro()
                    return
                
                if Config.USE_SAVED_POSITION: 
                    FileHandler.write(StaticVariables.region_filepath, json.dumps(self.saved_regions, indent=4))
                    logging.info(f"Region saved successfully as {screen_res_str}.")

                logging.info(f"Region '{screen_res_str}' selected successfully.")

            # region selected correctly #
            Variables.is_roblox_focused = False
            Variables.is_selecting_region = False
            Variables.minigame_region = region

        # window functions #
        def update_window_status(self, text, hint, circleColor): 
            self.ui.window.evaluate_js(f'updateStatus("{text}", "{hint}", "{circleColor}")')

        # hotkeys #
        def setup_hotkeys(self):
            if not Variables.is_running: return

            if current_os == "Darwin": # macos will crash for some reason
                logging.info("Global hotkeys disabled on macOS. You can stop the macro by closing the UI window.")
                return
            
            try:
                self.hotkeys = pynput.keyboard.GlobalHotKeys({ "<ctrl>+e": lambda: setattr(Variables, "is_running", False) })
                self.hotkeys.__enter__()

                logging.info("Global hotkeys enabled. Press Ctrl+E to stop the macro.")
            except Exception as e:
                logging.warning(f"Failed to setup global hotkeys: {e}")
                logging.info("You can stop the macro by closing the UI window.")

        # main function #
        def sell_all_items(self, was_last_key=False):
            if Config.PATHFINDING == True and Config.AUTO_SELL_AFTER_PATHFINDING_MACRO == True:
                if was_last_key:
                    logging.info("Selling items...")
                    self.update_window_status("Selling items...", f"Total selling attempts: {self.sell_handler.total_sold}", "green")

                    self.sell_handler.sell_items(Variables.dig_count)
                return

            not_sold = max(1, Variables.dig_count - self.sell_handler.total_sold)
            required = max(2, Config.AUTO_SELL_REQUIRED_ITEMS)
            can_sell = not_sold % required == 0
            if not can_sell: return

            logging.info(f"Selling items... {not_sold} % {required}")
            self.update_window_status("Selling items...", f"Total selling attempts: {self.sell_handler.total_sold}", "green")
            self.sell_handler.sell_items(Variables.dig_count)

        def start_minigame(self, equipped=False):
            if Variables.is_minigame_active: return
            if not Variables.is_roblox_focused: return

            logging.info("Starting minigame...")
            self.update_window_status("Starting minigame...", f"Total dig count: {Variables.dig_count}", "green")

            # start minigame #
            left_click()
            
            # waiting of max 1.5 sec #
            start = time.time()
            timed_out = False
            while Variables.is_running and Variables.is_roblox_focused:
                time.sleep(0)

                timed_out = (time.time() - start) > 1.5
                if Variables.is_minigame_active == True or timed_out: break
            
            logging.debug(f"Timed out: {(time.time() - start) > 1.5} | Active: {Variables.is_minigame_active} | Equipped: {equipped}")
            if not Variables.is_running or not Variables.is_roblox_focused: return
            
            if timed_out == True and Variables.is_minigame_active == False:
                if equipped == True:
                    self.update_window_status("Error", "Failed to start the minigame in the second try, waiting...", "red")
                    time.sleep(2.5)
                    return
                
                self.update_window_status("Error", "Failed to start the minigame!", "red")

                logging.info("Equipping shovel...")
                press_key("1") # equip the shovel #
                time.sleep(0.5)
                return self.start_minigame(equipped=True)


        def main_loop(self, _):
            print("Creating screenshot folders...")
            FileHandler.create_folder(StaticVariables.prediction_screenshots_path)

            while Variables.is_running:
                time.sleep(0.25)

                # handle idle_time, and skip if not in idle #
                if not Variables.is_idle():
                    if Variables.is_minigame_active:
                        self.update_window_status("Minigame", "Completing minigame...", "green")
                    
                    self.total_idle_time = 0
                else:
                    # main handler #
                    if Config.AUTO_REJOIN:
                        if Variables.is_rejoining: 
                            continue

                        if can_rejoin(self.total_idle_time):
                            self.update_window_status("Rejoining...", "Waiting for Roblox to load...", "yellow")

                            self.total_idle_time = 0
                            rejoin_dig()
                            continue

                    # skip main loop if roblox is not focused #
                    if not Variables.is_roblox_focused:
                        self.update_window_status("Waiting for Roblox Window Focus", "Please focus Roblox!", "red")
                        time.sleep(0.5)
                        continue

                    # handling dig_count and if digging finished #
                    digging_finished = False
                    if Variables.last_minigame_interaction is not None and Variables.last_minigame_interaction != -1:
                        last_interact = int(Variables.last_minigame_interaction) / 1000

                        if last_interact > 0 and (time.time() - last_interact) >= 1.5:
                            Variables.dig_count = Variables.dig_count + 1
                            Variables.last_minigame_interaction = None

                            logging.debug("Added 1 to dig_count, waiting..."); 
                            digging_finished = True

                            if Variables.sleep(0.75): break
                    else: digging_finished = True

                    # skip if digging didnt finish #
                    if not digging_finished: continue

                    self.finder.debug_img = None
                    self.total_idle_time += 0.25

                       # no dirt bar #
                    if self.finder.DirtBar.clickable_position is None:
                        self.update_window_status("Minigame", "Waiting for dirt bar...", "yellow")

                    elif self.finder.PlayerBar.current_position is None:
                        self.update_window_status("Minigame", "Waiting for player bar...", "yellow")

                    else:
                        self.update_window_status("Minigame", "Waiting for minigame...", "yellow")

                    # pathfinding handler #
                    was_last_key = False
                    if Config.PATHFINDING == True:
                        self.update_window_status("Pathfinding", "Walking to the next point...", "green")
                        was_last_key = self.pathfinding.start_walking()
                    
                    # auto sell #
                    if Config.AUTO_SELL == True: self.sell_all_items(was_last_key=was_last_key)

                    # minigame handler #
                    if Config.AUTO_START_MINIGAME == True: self.start_minigame()
            
            ###############################################################################################
            logging.info("Main loop has successfully ended.")
            self.ui.stop_window()

        # thread functions #
        def setup_finder_thread(self):
            if not Variables.is_running: return
            # add_function = self.add_function
            finder = self.finder

            class FinderThread(threading.Thread):
                def __init__(self):
                    super().__init__()

                    self.daemon = True
                    self._stop_event = threading.Event()

                def run(self):
                    logging.info("Finder loop started.")

                    frame_time = 1 / Config.TARGET_FPS
                    sct = mss.mss()
                    fps_counter = FPSCounter()

                    while not self._stop_event.is_set():
                        frame_start = time.perf_counter()
                        
                        # update state and click #
                        finder.update_state(sct)
                        finder.handle_click()
                        
                        fps_counter.accumulate_frame_time(frame_start)
                        finder.current_fps = fps_counter.get_fps()

                        elapsed = time.perf_counter() - frame_start
                        sleep_time = max(0, frame_time - elapsed)

                        if sleep_time > 0: time.sleep(sleep_time)

                    logging.info("Finder loop stopped successfully.")

                def stop(self): self._stop_event.set()
            
            thread = FinderThread()
            self.add_thread("finder_thread", thread=thread)
            thread.start()

        def setup_roblox_focused_thread(self):
            if not Variables.is_running: return

            class RobloxFocusThread(threading.Thread):
                def __init__(self):
                    super().__init__()

                    self.daemon = True
                    self._stop_event = threading.Event()

                def run(self):
                    logging.info("Roblox focus loop started.")

                    while not self._stop_event.is_set():
                        Variables.is_roblox_focused = is_roblox_focused()
                        time.sleep(0.25)

                    logging.info("Roblox focus loop stopped successfully.")

                def stop(self): self._stop_event.set()
            
            thread = RobloxFocusThread()
            self.add_thread("roblox_focused_thread", thread=thread)
            thread.start()
        
        # cleanup function #
        def exit_macro(self):
            logging.info("-------------- EXIT --------------")
            Variables.is_running = False

            screenshot_cleanup()

            # stop hotkeys #
            if self.hotkeys:
                try:
                    logging.info("Stopping hotkeys...")
                    self.hotkeys.__exit__(None, None, None)
                    logging.info("Hotkeys stopped.")
                except Exception as e: logging.warning(f"Error stopping hotkeys: {traceback.format_exc()}")

            # stop threads #
            logging.info("Stoping threads...")
            failed_threads = []
            for thread in self.active_threads:
                if self.stop_thread(thread): continue
                failed_threads.append(thread)

            if len(failed_threads) > 0: logging.warning(f"Failed to stop {len(failed_threads)} threads...")
            
            # stop UI #
            logging.info("Closing UI...")
            for ui in [self.ui, self.region_check_ui, self.guide_ui]:
                if not ui: continue

                try:
                    logging.info("Closing UI window...")
                    ui.stop_window()
                    logging.info("UI window closed")
                except Exception as e: logging.warning(f"Error closing UI window: {traceback.format_exc()}")

            # call cleaning functions #
            logging.info("Calling cleanup functions...")
            for func in self.cleanup_functions:
                try:
                    logging.info(f"Calling cleanup function: {func.__name__}")
                    func()
                except Exception as e: logging.warning(f"Error in cleanup function: {func.__name__}: {str(e)}")

            # clear empty files/folders #
            for (folderpath, is_empty) in FileHandler.get_folders(StaticVariables.screenshots_path):
                if is_empty == True: FileHandler.try_delete_folder(folderpath)

    # load main macro handler #
    macro = MacroHandler()

    if Config.AUTO_SELL == True and Config.AUTO_SELL_BUTTON_POSITION == (0, 0):
        msgbox.alert("Invalid button position selected for Auto Sell. Auto Sell has been disabled.", bypass=True)
        Config.AUTO_SELL = False
    
    # region #
    macro.setup_finder_thread()
    macro.setup_region_setter()

    # run threads #
    macro.setup_roblox_focused_thread()

    # setup hotkeys #
    macro.setup_hotkeys()

    # load ui #
    if Variables.is_running:
        logging.info("Loading UI...")
        macro.ui.start(macro.main_loop)
        macro.exit_macro()
    
    logging.info("----------------- STOPPED ------------------")
    os.kill(os.getpid(), 9)