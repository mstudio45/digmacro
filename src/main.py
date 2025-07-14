# imports #
import os, sys, time, traceback, subprocess, platform

current_os = platform.system() # Linux, Windows, Darwin
if current_os not in ["Linux", "Darwin", "Windows"]:
    print(f"Current OS '{current_os}' is not supported.")
    sys.exit(0)

compiled = "__compiled__" in globals()
def restart_macro(args=["--skip-selection"]):
    final_exe, final_args = "", []

    if compiled:
        final_exe = sys.argv[0]
        final_args = args
    else:
        final_exe = sys.executable
        final_args = [sys.executable, os.path.abspath(__file__)] + args

    print(f"Restarting: {final_exe} {final_args}")
    try:
        import logging
        logging.info(f"Restarting: {final_exe} {final_args}")
    except: pass
    
    os.execvp(final_exe, final_args)
    return

# install requirements #
from utils.packages.check_apt import check_apt_packages
from utils.packages.check_errors import check_special_errors
from utils.packages.check_python import check_pip_packages
from utils.packages.check_shutil import check_shutil_applications
from utils.packages.versions import check_package_version

if "--skip-install" not in sys.argv:
    if "--only-install" in sys.argv: 
        check_shutil_applications()
        check_apt_packages()
        check_pip_packages()
        os.kill(os.getpid(), 9)

    if check_shutil_applications() or check_apt_packages() or check_pip_packages():
        restart_macro(["--skip-install"])
        sys.exit(0)
else: logging.info("Package installation skipped.")

check_special_errors() # still required to run, fixes for tkinter on windows #

# imports #
import logging, threading
import cv2, webbrowser
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

# set DPI awareness #
if current_os == "Windows":
    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwarenessContext(-4)
        logging.info("SetProcessDpiAwarenessContext to PER_MONITOR_AWARE_V2")
    except AttributeError: # fallback for older win versions
        try:
            ctypes.windll.user32.SetProcessDPIAware()
            logging.info("SetProcessDPIAware to System Aware")
        except Exception as e:
            msgbox.alert(f"Could not set DPI awareness: {e}", log_level=logging.ERROR, bypass=True)

if __name__ == "__main__":
    # macOS Permission Checks (thanks SalValichu) #
    if current_os == "Darwin":
        try:
            from ApplicationServices import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt # type: ignore
            message_check = (
                "This application requires '{permission}' permission to control mouse and keyboard.\n\n"
                "Please go to:\nSystem Settings -> Privacy & Security -> {permission}\n" 
                "Then, ensure this application (digmacro_macosarm64, digmacro_macosx86_64 or Python Launcher/Python) is enabled.\n\n" 
                "Press 'OK' after enabling '{permission}' permission, the macro will restart itself.\n" 
                "If the permission is enabled and you are still being prompted with this notification, press 'Skip'"
            )

            # Check Accessibility #
            if not AXIsProcessTrustedWithOptions({ kAXTrustedCheckOptionPrompt: True }): # this will also prompt the notification to allow the permission #
                # if it goes here the user didn't select "Allow" # 
                logging.info("[macOS Permissions] Accessibility access is required, prompting user to enable it.")
                res = msgbox.confirm(
                    message_check.replace("{permission}", "Accessibility"),
                    title="DIGMacro - Permission Issue",
                    buttons=("OK", "Skip", "Exit")
                )

                if res == "OK":
                    restart_macro()
                    sys.exit(0)
                else: os.kill(os.getpid(), 9) # exit if user didnt select OK #
            else: logging.info("[macOS Permissions] Accessibility access is enabled.")

            # Check Screen Recording (we will try to make an screenshot - mss should prompt that allow notification) #
            try:
                with mss.mss() as sct:
                    monitor = sct.monitors[0]
                    sct.grab(monitor)
                    sct.close()
                
                logging.info("[macOS Permissions] Screen Recording check permission appears granted.")
            except Exception as e:
                logging.warning(f"[macOS Permissions] Screen Recording check failed: {e}")
                logging.info("[macOS Permissions] Screen Recording access is required, prompting user to enable it.")

                res = msgbox.confirm(
                    message_check.replace("{permission}", "Screen Recording"),
                    title="DIGMacro - Permission Issue",
                    buttons=("OK", "Skip", "Exit")
                )
                if res == "OK":
                    restart_macro()
                    sys.exit(0)
                else: os.kill(os.getpid(), 9) # exit if user didnt select OK #

            # we will skip input monitoring permission, the user needs to use their keyboard and mouse for the test to work #
            # it will be pretty annoying for the user to do that each macro restart #
            # pynput should however prompt that permission notification #
        except ImportError:     logging.warning("[macOS Permissions] Could not import ApplicationServices for permission check. Skipping...")
        except Exception as e:  logging.error(f"[macOS Permissions] Error during permission check: {e}")

    # create folders (on macOS it will prompt an allow 'folder' access notification) #
    print("Creating storage folder...")
    FileHandler.create_folder("storage")

    print("Creating logs folder...")
    FileHandler.create_folder(StaticVariables.logs_path)

    print("Loading config...")
    Config.load_config() # default_config_loaded

    from utils.logs import setup_logger, disable_spammy_loggers
    print("Loading logger...")
    setup_logger()

    logging.info("Loading screen information...")
    from utils.images.screenshots import screenshot_cleanup
    from utils.images.screen import screen_res_str

    ## check version ##
    current_version = "2.0.2"
    current_branch = "main"

    try:
        logging.info("Checking current version...")

        import requests, json
        req = requests.get("https://raw.githubusercontent.com/mstudio45/digmacro/refs/heads/storage/versions.json", timeout=2.5)
        versions = json.loads(req.text)

        # check versions #
        if current_branch not in versions: raise Exception(f"{current_branch} is not an valid branch.")
        latest_branch_version = versions[current_branch]
        is_outdated = check_package_version(latest_branch_version, current_version, check_if_equal=False)

        logging.info(f"Running on '{current_branch}' - {current_version} | Latest '{current_branch}' version: {latest_branch_version} | {latest_branch_version} > {current_version} = {is_outdated}")
        if is_outdated:
            res = msgbox.confirm(f"A new version is avalaible at https://github.com/mstudio45/digmacro!\n{current_version} -> {latest_branch_version}\nDo you want to open the Github repository?\n\n -- If you encounter any issues don't report them, you are using an outdated version. -- ")
            if res == "Yes":
                try:
                    if current_os == "Windows":
                        webbrowser.open("https://github.com/mstudio45/digmacro")
                    else:
                        subprocess.run([Variables.unix_open_app_cmd, "https://github.com/mstudio45/digmacro"])
                except Exception as e: logging.error(f"Failed to open link: {e}")
    except Exception as e:
        msgbox.alert(f"Failed to check for new updates. {str(e)}", bypass=True)

    run_config = False

    if "--skip-selection" in sys.argv or "--region-check" in sys.argv:
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
            
            # exit or restart #
            if config_ui.start_macro_now == True: restart_macro()
            else:                                 os.kill(os.getpid(), 9)
        
        elif res == "Exit" or res == "": os.kill(os.getpid(), 9)
        else: logging.info("Starting the macro...")

    # log opencv info #
    logging.info("===============================")

    logging.debug(cv2.getBuildInformation())
    logging.info("Optimizing opencv...")

    try:
        logging.info(f"Optimized: {cv2.useOptimized()} - Threads: {cv2.getNumThreads()} - CPUs: {cv2.getNumberOfCPUs()}")

        cv2.setUseOptimized(True)
        cv2.setNumThreads(cv2.getNumberOfCPUs())

        logging.info(f"Optimized: {cv2.useOptimized()} - Threads: {cv2.getNumThreads()} - CPUs: {cv2.getNumberOfCPUs()}")
    except Exception as e: logging.critical(f"Failed to optimize opencv: {str(e)}")
    
    # try:
    #     time.sleep(0.1)
    #     logging.info("Enabling OpenCL...")
    #     cv2.ocl.setUseOpenCL(True)
    # except Exception as e: logging.critical(f"Failed to optimize opencv (#2): {str(e)}")

    logging.info("===============================")

    # main loader #
    logging.info("Importing libraries...")
    from utils.finder import MainHandler, SellUI
    from utils.pathfinding import PathfingingHandler

    from utils.input.mouse import left_click
    from utils.input.keyboard import press_key

    from utils.roblox.rejoin import rejoin_dig, can_rejoin
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

            self.last_text = ""
            self.last_hint = ""

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
                thread_name = "???"
                if thread.name is not None: thread_name = thread.name
                
                logging.warning(f"Warning: Thread '{thread_name}' did not stop gracefully.")
                return False
            
            return True

        # functions handler #
        def add_function(self, func):
            if func in self.cleanup_functions: return
            self.cleanup_functions.append(func)

        # region selector #
        def check_saved_region(self):
            self.region_key = f"{current_os} {screen_res_str}" # TO-DO: Windows MonitorID:0x0 1920x1080
            logging.info(f"Checking saved region: {self.region_key}...")

            if Config.USE_SAVED_POSITION == False or not os.path.isfile(StaticVariables.region_filepath):
                logging.info("Saved regions are disabled or storage/region.json file doesn't exist.")
                return None
            
            try:
                pos = FileHandler.read(StaticVariables.region_filepath)
                if pos is not None and isinstance(pos, str) and pos != "":
                    self.saved_regions = json.loads(pos)

                    if self.region_key in self.saved_regions:
                        region = self.saved_regions[self.region_key]

                        if "left" in region and "top" in region and "width" in region and "height" in region:
                            logging.info(f"Using saved region '{self.region_key}'.\n")
                            return region
                        else:
                            logging.info(f"Invalid region found: '{self.region_key}', it will be deleted.\n")
                            self.saved_regions[self.region_key] = None
                        ##########################################################################
                    else: logging.info(f"{self.region_key} doesn't exist, will prompt region selector.\n")
                else: logging.info("Failed to read region file/Invalid data found inside region file.\n")
            except Exception as e: msgbox.alert(f"Failed to load saved position: \n{str(e)}", log_level=logging.ERROR)

            return None
        
        def setup_region_setter(self): # requires to be run in main thread #
            logging.info("Loading region setter...")
            region = self.check_saved_region()
            
            if "--region-check" in sys.argv:
                logging.info("Loading region check...")
                if region is None:
                    msgbox.alert("Invalid region, you need to have a saved region.", bypass=True)
                    self.exit_macro()
                    sys.exit(1)

                Variables.minigame_region = region
                self.finder.setup_region_image_size()
                
                logging.info("Loading region check UI...")
                self.region_check_ui.start()
                self.exit_macro()
                sys.exit(0)

            logging.info(f"Saved region: {region}")
            if region is None:
                # load guide #
                if "--skip-guide-ui" not in sys.argv:
                    logging.info("Showing guide...")

                    self.guide_ui.start()
                    if not Variables.is_running or self.guide_ui.is_running == False:
                        self.exit_macro()
                        return
                else: logging.info("Guide UI skipped.")

                # start region select #
                logging.info("Starting region selection...")
                self.region_selector.start()
                region = self.region_selector.get_selection()
                if region is None:
                    self.exit_macro()
                    return

                logging.info("Region has been set.")
                region["height"] = max(16, region["height"]) # required for player bar aspect ratio checking #
                Variables.minigame_region = region
                self.saved_regions[self.region_key] = region
                self.finder.setup_region_image_size()

                # load region select checker ui #
                logging.info("Loading region check UI...")
                self.region_check_ui.start()
                if self.region_check_ui.restart_macro:
                    self.exit_macro()
                    restart_macro(["--skip-selection", "--skip-guide-ui", "--skip-install"])
                    return
                
                if self.region_check_ui.is_okay == False:
                    self.exit_macro()
                    return
                
                if Config.USE_SAVED_POSITION: 
                    FileHandler.write(StaticVariables.region_filepath, json.dumps(self.saved_regions, indent=4))
                    logging.info(f"Region saved successfully as {self.region_key}.")

                logging.info(f"Region '{self.region_key}' selected successfully.")

            # region selected correctly #
            logging.info("Region has been loaded successfully.\n")
            Variables.is_roblox_focused = False
            Variables.is_selecting_region = False
            Variables.minigame_region = region
            self.finder.setup_region_image_size()

        # window functions #
        def update_window_status(self, text, hint, circleColor):
            if (text == "" and hint == "") or text != self.last_text or hint != self.last_hint: # prevent update spam #
                self.last_text = text
                self.last_hint = hint

                logging.debug(f"[UI STATUS - {circleColor}] {text}: {hint}")
                self.ui.window.evaluate_js(f'updateStatus("{text}", "{hint}", "{circleColor}")')

        # hotkeys #
        def setup_hotkeys(self):
            if not Variables.is_running: return

            if current_os == "Darwin": # macos will crash for some reason
                logging.info("Global hotkeys disabled are currently disabled on macOS. You can stop the macro by closing the UI window.\n")
                return
            
            try:
                self.hotkeys = pynput.keyboard.GlobalHotKeys({ "<ctrl>+e": lambda: setattr(Variables, "is_running", False) })
                self.hotkeys.__enter__()

                logging.info("Global hotkeys enabled. Press Ctrl+E to stop the macro.\n")
            except Exception as e:
                msgbox.alert(f"Failed to setup global hotkeys: {str(e)}", bypass=True)
                logging.info("You can stop the macro by closing the UI window.\n")

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
            time.sleep(0.1)
            left_click()
            
            # waiting of max 1.5 sec #
            start = time.time()
            timed_out = False
            while Variables.is_running and Variables.is_roblox_focused:
                time.sleep(0)

                timed_out = (time.time() - start) > 1.5
                if Variables.is_minigame_active == True or timed_out: break
            
            logging.info(f"Timed out: {(time.time() - start) > 1.5} | Active: {Variables.is_minigame_active} | Equipped: {equipped}")
            if not Variables.is_running or not Variables.is_roblox_focused: return
            
            if timed_out == True and Variables.is_minigame_active == False:
                if equipped == True:
                    self.update_window_status("Error", "Failed to start the minigame in the second try, waiting...", "red")
                    time.sleep(2.5)
                    return
                
                self.update_window_status("Error", "Failed to start the minigame!", "red")

                logging.info("Equipping shovel...")
                press_key("1") # equip the shovel #
                time.sleep(0.8)
                return self.start_minigame(equipped=True)

        def main_loop(self, _):
            logging.info("Creating screenshot folders...")
            FileHandler.create_folder(StaticVariables.prediction_screenshots_path)

            # TO-DO: switch to pause system
            logging.info("Waiting for Roblox to be focused atleast once for the macro to start...")
            while not Variables.is_roblox_focused:
                self.update_window_status("Waiting for Roblox Window Focus", "Focus Roblox to start the macro...", "yellow")
                if Variables.sleep(1): break
                continue
            
            time.sleep(0.5)
            if Variables.is_running: 
                while Variables.is_running:
                    time.sleep(0.25)

                    # handle idle_time, and skip if not in idle #
                    if not Variables.is_idle():
                        if Variables.is_minigame_active:
                            self.update_window_status("Minigame", "Completing minigame...", "green")
                        
                        self.total_idle_time = 0
                    else: # main handler #

                        if Config.AUTO_REJOIN:
                            if Variables.is_rejoining: continue

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
                        if self.finder.minigame_detected_by_avg == False:
                            self.update_window_status("Minigame", "Waiting for minigame to be detected...", "yellow")

                        elif self.finder.DirtBar.clickable_position is None:
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
                        if Config.AUTO_SELL == True: 
                            self.sell_all_items(was_last_key=was_last_key)

                        # minigame handler #
                        if Config.AUTO_START_MINIGAME == True: 
                            self.start_minigame()
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

            logging.info("----------- CLEANUP DONE -------------")

    # load main macro handler #
    logging.info("Loading MacroHandler...")
    macro = MacroHandler()

    # verify configuration #
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
        disable_spammy_loggers()

        logging.info("Loading UI...")
        macro.ui.start(macro.main_loop)
        macro.exit_macro()
    
    logging.info("----------------- STOPPED ------------------")
    os.kill(os.getpid(), 9)