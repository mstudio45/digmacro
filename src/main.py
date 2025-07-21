# imports #
import os, sys, time, traceback, subprocess, platform

current_os = platform.system() # Linux, Windows, Darwin
if current_os not in ["Linux", "Darwin", "Windows"]:
    print(f"Current OS '{current_os}' is not supported.")
    sys.exit(0)

compiled = "__compiled__" in globals()
def restart_macro(args=["--skip-selection"]):
    final_exe, final_args = "", []

    if current_os == "Darwin":
        final_exe = sys.argv[0]
        final_args = args
    
        if ".app/Contents/MacOS" in __file__:
            try:
                from AppKit import NSBundle # type: ignore
                bundle = NSBundle.mainBundle()

                if bundle and bundle.executablePath():
                    final_exe = str(bundle.executablePath())
                    final_args = args
            except: 
                final_exe = sys.argv[0]
                final_args = args
    else:
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
from utils.packages.distro_variables import log_install, close_log_file
from utils.packages.check_apt import check_apt_packages
from utils.packages.check_errors import check_special_errors
from utils.packages.check_python import check_pip_packages
from utils.packages.check_shutil import check_shutil_applications
from utils.packages.versions import is_version_outdated

if "--skip-install" not in sys.argv:
    if "--only-install" in sys.argv:
        log_install("Only installing packages...")

        check_shutil_applications()
        check_apt_packages()
        check_pip_packages()

        close_log_file()
        os.kill(os.getpid(), 9)

    if check_shutil_applications() or check_apt_packages() or check_pip_packages():
        close_log_file()

        restart_macro(["--skip-install"])
        sys.exit(0)
else: log_install("Package installation skipped.")

check_special_errors() # still required to run, fixes for tkinter on windows #
close_log_file()

# load config and logging #
from variables import Variables, StaticVariables
from config import Config

from utils.logs import setup_logger, disable_spammy_loggers
import utils.general.filehandler as FileHandler

# create folders (on macOS it will prompt an allow 'folder' access notification) #
FileHandler.create_folder(StaticVariables.storage_folder)
FileHandler.create_folder(StaticVariables.logs_path)

Config.load_config() # default_config_loaded
setup_logger()

# imports #
import logging, threading
import webbrowser
import pyautogui, mss
import interface.msgbox as msgbox

try: import cv2
except ImportError as e:
    if "numpy" in str(e):
        import numpy as np
        import cv2
    else: raise e

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
            msgbox.alert(f"Could not set DPI awareness: {e}", log_level=logging.ERROR)

if __name__ == "__main__":
    # macOS Permission Checks (thanks SalValichu) #
    if current_os == "Darwin":
        logging.info("[macOS Permissions] Checking permission...")

        try:
            import objc # type: ignore
            from ApplicationServices import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt # type: ignore
            import Quartz # type: ignore
            from Quartz import CGPreflightScreenCaptureAccess, CGRequestScreenCaptureAccess # type: ignore # used for screen recording
            
            # used for input monitoring #
            kIOHIDRequestTypeListenEvent = 1
            kIOHIDAccessTypeGranted = 0
            kIOHIDAccessTypeDenied = 1
            kIOHIDAccessTypeUnknown = 2

            # arch = platform.machine()
            message_check = (
                "This application requires '{permission}' permission to {why}.\n\n"

                "Please go to: System Settings -> Privacy & Security -> {permission}\n"
                f"Then, ensure this application (digmacro_macos_universal) is enabled.\n"
                "⚠ If you are opening the macro with Terminal (or any other application), ensure that application also have '{permission}' permission enabled. ⚠\n\n"

                "Press 'OK' after enabling '{permission}' permission, the macro will restart itself.\n"
                "If the permission is enabled and you are still being prompted with this notification, press 'Skip'."
            )

            # Functions #
            def has_accessibility_access(prompt=False):
                options = { kAXTrustedCheckOptionPrompt: prompt }
                return AXIsProcessTrustedWithOptions(options)
            
            def has_input_monitor_access(): # macOS 10.15+
                try:
                    import ctypes
                    iokit = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/IOKit.framework/IOKit')
                    return iokit.IOHIDCheckAccess(kIOHIDRequestTypeListenEvent) == kIOHIDAccessTypeGranted
                except Exception as e:
                    logging.info(f"Failed to check Input Monitoring: {str(e)}")
                    return True # just assume its enabled #
            
            def prompt_issue_msgbox(permission, why):
                logging.info(f"[macOS Permissions] {permission} access is required, prompting user to enable it.")

                # open the settings page #
                try: subprocess.check_call(["open", "x-apple.systempreferences:com.apple.preference.security"])
                except Exception as e: logging.warning(f"[macOS Permissions] Failed to open system preferences: {str(e)}")

                # warn the user #
                res = msgbox.confirm(
                    message_check.replace("{permission}", permission).replace("{why}", why),
                    title="DIGMacro - Permission Issue",
                    buttons=("OK", "Skip", "Exit")
                )

                if res == "OK":
                    restart_macro(["--skip-install"])
                    sys.exit(0)
                    return
                elif res == "Skip":
                    print("Skipped...")
                else:
                    os.kill(os.getpid(), 9)
                    return

            # Accessibility #
            if has_accessibility_access(False): # only check #
                logging.info("[macOS Permissions] Accessibility access is enabled.")
            else:
                # has_accessibility_access(True)
                prompt_issue_msgbox("Accessibility", "control mouse and keyboard")

            # Screen Recording #
            if CGPreflightScreenCaptureAccess(): # only check #
                logging.info("[macOS Permissions] Screen Recording access is enabled.")
            else:
                # CGRequestScreenCaptureAccess()
                prompt_issue_msgbox("Screen Recording", "detect the minigame")
            
            # Input Monitoring #
            if has_input_monitor_access(): # only check #
                logging.info("[macOS Permissions] Input Monitoring access is enabled.")
            else:
                prompt_issue_msgbox("Input Monitoring", "allow global hotkeys")
            
        except ImportError as e: logging.warning(f"[macOS Permissions] Could not import packages for permission check. Skipping... {str(e)}")
        except Exception as e:   logging.error(f"[macOS Permissions] Error during permission check: {str(e)}")

    logging.info("Loading screen information...")
    from utils.images.screenshots import screenshot_cleanup
    from utils.images.screen import screen_res_str, screen_region

    ## check version ##
    try:
        logging.info("Checking current version...")

        import requests, json
        req = requests.get("https://raw.githubusercontent.com/mstudio45/digmacro/refs/heads/storage/versions.json", timeout=2.5)
        versions = json.loads(req.text)

        # check versions #
        if Variables.current_branch not in versions: raise Exception(f"{Variables.current_branch} is not an valid branch.")
        latest_branch_version = versions[Variables.current_branch]
        is_outdated = is_version_outdated(Variables.current_version, latest_branch_version)

        logging.info(f"Running on '{Variables.current_branch}' - {Variables.current_version} | Latest '{Variables.current_branch}' version: {latest_branch_version} | {latest_branch_version} > {Variables.current_version} = {is_outdated}")
        if is_outdated:
            res = msgbox.confirm(f"A new version is avalaible at https://github.com/mstudio45/digmacro!\n{Variables.current_version} > {latest_branch_version}\nDo you want to open the Github repository?\n\n -- If you encounter any issues don't report them, you are using an outdated version. -- ")
            if res == "Yes":
                try:
                    if current_os == "Windows":
                        webbrowser.open("https://github.com/mstudio45/digmacro")
                    else:
                        subprocess.run([Variables.unix_open_app_cmd, "https://github.com/mstudio45/digmacro"])
                except Exception as e: logging.error(f"Failed to open link: {e}")
    except Exception as e:
        msgbox.alert(f"Failed to check for new updates. {str(e)}")

    # selection handler #
    run_config = "--open-config" in sys.argv

    if "--skip-selection" in sys.argv or "--region-check" in sys.argv:
        logging.info("Skipping config/start selection.")
    else:
        if run_config == False:
            res = msgbox.confirm("What would you like to do?", buttons=("Start Macro", "Edit the configuration", "Exit"))
            if res == "Edit the configuration":
                run_config = True
            elif res == "Exit" or res == "": 
                os.kill(os.getpid(), 9)
            else: 
                logging.info("Starting the macro...")

        # start configuration #
        if run_config == True:
            # config ui #
            logging.info("Loading Config GUI...")
            if current_os == "Linux":
                os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = ""
                os.environ["QT_STYLE_OVERRIDE"] = "fusion"

            from interface.config_ui import ConfigUI
            from PySide6.QtWidgets import QApplication

            q_app = QApplication(sys.argv)
            config_ui = ConfigUI()
            config_ui.show()
            q_app.exec()
            
            # exit or restart #
            if config_ui.start_macro_now == True: restart_macro()
            else:                                 os.kill(os.getpid(), 9)
    #############################################################################

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
    from utils.input.mouse import left_click, move_mouse, _pynput_mouse_controller
    from utils.input.keyboard import press_key, setup_global_hotkeys

    from utils.detectors.handler import MainHandler
    from utils.sellinv import SellUI
    from utils.pathfinding import PathfingingHandler

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

            # risk spin :boom: #
            self.risk_spin_tuple = None

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
                    msgbox.alert("Invalid region, you need to have a saved region.")
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
            logging.info("Loading Global Hotkeys...")

            try:
                # functions #
                def close_hotkey(): setattr(Variables, "is_running", False)
                def pause_hotkey(): self.ui.pause()

                # start #
                self.hotkeys = setup_global_hotkeys({ 
                    "<ctrl>+e": close_hotkey,
                    "<ctrl>+p": pause_hotkey
                })

                logging.info("Global hotkeys enabled. Press Ctrl+E to stop the macro.\n")
            except Exception as e:
                msgbox.alert(f"Failed to setup global hotkeys: {str(e)}")
                logging.info("You can stop the macro by closing the UI window.\n")

        # main function #
        def sell_all_items(self):
            not_sold = max(1, Variables.dig_count - self.sell_handler.total_sold)
            required = max(2, Config.AUTO_SELL_REQUIRED_ITEMS)
            can_sell = not_sold % required == 0

            if can_sell:
                logging.info(f"Auto Sell Information: {not_sold} % {required} == 0 -> {can_sell}")
                self.update_window_status("Selling items...", f"Total selling attempts: {self.sell_handler.total_sold}", "green")
                self.sell_handler.sell_items(Variables.dig_count)

        def re_equip_shovel(self):
            press_key("2") # equip something else #
            time.sleep(0.75) # wait #
            press_key("1") # equip the shovel #
            time.sleep(0.75) # wait #

        def start_minigame(self, failed_do_equip=False):
            if Variables.is_minigame_active:     
                logging.info("Minigame is already active, skipping...")
                return
            # else:
            #     if self.total_idle_time < 0.2:
            #         logging.info("Not inactive for long enough, skipping...")
            #         return
            
            if not Variables.is_roblox_focused: logging.info("Roblox is not focused, skipping..."); return

            logging.info("Starting minigame...")
            self.update_window_status("Starting minigame...", f"Total dig count: {Variables.dig_count}", "green")

            # handle shovel re-equipping #
            if failed_do_equip == True: self.re_equip_shovel()

            # start the minigame #
            if Variables.is_minigame_active:
                logging.info("Minigame started successfully!")
                time.sleep(0.25)
                return
            
            left_click()
            
            # wait for the minigame to start #
            start_time = time.time()
            while Variables.is_running and Variables.is_roblox_focused:
                if Variables.is_minigame_active: break
                
                # check for timeout #
                elapsed_time = time.time() - start_time
                if elapsed_time > 1.75:
                    logging.warning(f"Minigame start timed out after {elapsed_time:.2f}s...")
                    break
                    
                time.sleep(0.01)

            # re-check the current state #
            if Variables.is_minigame_active:
                logging.info("Minigame started successfully!")
                time.sleep(0.25)
                return
            
            if not Variables.is_running or not Variables.is_roblox_focused:
                logging.info("Roblox is no longer focused or the macro is stopping, aborting...")
                return
            
            if failed_do_equip == True:
                Variables.failed_minigame_attempts = Variables.failed_minigame_attempts + 1
                self.update_window_status("Error", "Failed to start minigame after the second try...", "red")
                return
            
            # restart the function to equip #
            logging.info("First attempt failed, trying to equip shovel...")
            self.update_window_status("Minigame", "Equipping shovel...", "yellow")
            time.sleep(0.1)

            return self.start_minigame(failed_do_equip=True)

        def main_loop(self, _):
            logging.info("Creating screenshot folders...")
            FileHandler.create_folder(StaticVariables.prediction_screenshots_path)

            failed_risk_attemps = 0
            while Variables.is_running:
                time.sleep(0.1)

                # handle idle_time, and skip if not in idle #
                if Variables.is_paused == True:
                    self.update_window_status("Paused", "Resume to continue...", "gray")
                    self.total_idle_time = 0

                    while Variables.is_paused: 
                        if Variables.sleep(1): break
                    if not Variables.is_running: break

                elif Variables.is_minigame_active:
                    self.update_window_status("Minigame", "Completing minigame...", "green")

                    while Variables.is_running:
                        first_int = Variables.last_minigame_detection
                        if Variables.sleep(1): break

                        if first_int == Variables.last_minigame_detection: break # ended
                        if not Variables.is_minigame_active: break

                    if not Variables.is_running: break
                    failed_risk_attemps = 0
                    
                elif not Variables.is_idle():
                    self.update_window_status("Idle", "Waiting for minigame...", "yellow")
                    self.total_idle_time = 0
                    time.sleep(0.75)

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
                    if Variables.last_minigame_detection is not None and Variables.last_minigame_detection != -1:
                        last_interact = int(Variables.last_minigame_detection) / 1000
                        if last_interact > 0 and (time.time() - last_interact) >= 1.0:
                            Variables.dig_count = Variables.dig_count + 1
                            Variables.last_minigame_detection = None

                            logging.info("Added 1 to dig_count, waiting...")
                            logging.info("========= STARTING AUTO HANDLERS =========")
                            digging_finished = True
                            if Variables.sleep(0.75): break

                    else: digging_finished = True

                    # skip if digging didnt finish #
                    if not digging_finished: continue

                    self.finder.debug_img = None
                    self.total_idle_time += 0.1

                    # no dirt bar #
                    if self.finder.minigame_detected_by_avg == False:
                        self.update_window_status("Minigame", "Waiting for minigame to be detected...", "yellow")

                    elif self.finder.DirtBar.clickable_position is None:
                        self.update_window_status("Minigame", "Waiting for dirt bar...", "yellow")

                    elif self.finder.PlayerBar.current_position is None:
                        self.update_window_status("Minigame", "Waiting for player bar...", "yellow")

                    else:
                        self.update_window_status("Minigame", "Waiting for minigame...", "yellow")

                    # auto sell #
                    if Config.AUTO_SELL == True: 
                        self.sell_all_items()

                    # pathfinding handler #
                    if Config.PATHFINDING == True:
                        self.update_window_status("Pathfinding", "Walking to the next point...", "green")   

                        if self.pathfinding.current_macro == "risk_spin":
                            if self.risk_spin_tuple is None:
                                self.risk_spin_tuple = (screen_region["width"] // 2, screen_region["height"] // 2, 100 * (screen_region["width"] / 1280))
                                # 100 pixel is only for 2560x1440 so get scale factor for that #

                            middle_x, middle_y, offset = self.risk_spin_tuple

                            move_mouse(middle_x, middle_y, steps=1)
                            move_mouse(middle_x + offset, middle_y, delay=0.0125)
                            left_click()
                            move_mouse(middle_x - offset, middle_y, delay=0.005)
                            time.sleep(1)

                            failed_risk_attemps = failed_risk_attemps + 1 # let's assume its not working, if minigame starts it gets reset to 0 #
                            if failed_risk_attemps >= 5:
                                logging.info("Failed to do risk spin, adding 1 to failed_minigame_attempts and re-equipping the shovel...")
                                Variables.failed_minigame_attempts = Variables.failed_minigame_attempts + 1
                                failed_risk_attemps = 0
                                self.re_equip_shovel()
                            
                            continue
                        else:
                            self.pathfinding.start_walking()

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
                        if finder.update_state(sct) == True:
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
                    self.hotkeys.stop()
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
    if Config.AUTO_SELL == True and Config.AUTO_SELL_MODE == "Mouse Movement" and Config.AUTO_SELL_BUTTON_POSITION == (0, 0):
        msgbox.alert("Invalid button position selected for Auto Sell. Auto Sell has been disabled.")
        Config.AUTO_SELL = False

    if current_os != "Windows" and Config.PATHFINDING == True and Config.PATHFINDING_MACRO == "risk_spin":
        msgbox.alert("Pathfinding macro 'risk_spin' only works on Windows. Pathfinding has been disabled.")
        Config.PATHFINDING = False

    if Config.AUTO_SELL == True and Config.AUTO_SELL_AFTER_PATHFINDING_MACRO == True and Config.PATHFINDING == True:
        if Config.PATHFINDING_MACRO != "risk_spin" and Config.PATHFINDING_MACRO in Config.PathfindingMacros:
            Config.AUTO_SELL_REQUIRED_ITEMS = len(Config.PathfindingMacros[Config.PATHFINDING_MACRO]) + 1
            logging.info(f"Auto Sell (After Pathfinding) enabled, will sell after: {Config.AUTO_SELL_REQUIRED_ITEMS} items (amount of keys + 1)")

    if Config.AUTO_START_MINIGAME == False and Config.PATHFINDING == True and Config.PATHFINDING_MACRO == "risk_spin":
        msgbox.alert("You need to have 'AUTO_START_MINIGAME' minigame enabled to use 'risk_spin' pathfinding macro. Pathfinding has been disabled.")
        Config.PATHFINDING = False

    if Config.PATHFINDING == True and Config.PATHFINDING_MACRO == "risk_spin":
        msgbox.alert("Make sure shiftlock is enabled for the pahtfinding macro to work correctly!")

        if current_os == "Windows":
            logging.info("Disabling Mouse Acceleration/Enhance pointer precision...")

            import ctypes
            def switch_mouse_acceleration(turn_on=False):
                turn_on = int(turn_on == True)
                pv_param = (ctypes.c_int * 3)()

                if not ctypes.windll.user32.SystemParametersInfoW(0x0003, 0, pv_param, 0): return False # SPI_GETMOUSE
                if pv_param[2] == turn_on: return True # already set to what we want #
                
                # set the state #
                pv_param[2] = turn_on
                if not ctypes.windll.user32.SystemParametersInfoW(0x0004, 0, pv_param, 0x0002): return False # SPI_SETMOUSE, SPIF_SENDCHANGE

                return True

            logging.info("Disabling Mouse Acceleration/Enhance pointer precision...")
            if switch_mouse_acceleration(False) == False:
                msgbox.alert("Failed to disable 'Mouse Acceleration/Enhance pointer precision', disable it manually. Pathfinding has been disabled.")
                Config.PATHFINDING = False
            else:
                logging.info("Mouse Acceleration/Enhance disabled.")
        else:
            msgbox.alert("Pathfinding macro 'risk_spin' only works on Windows. Pathfinding has been disabled.")
            Config.PATHFINDING = False

    # notify user #
    # arch = platform.machine()
    # if current_os == "Darwin" and (arch == "i386" or arch == "x86_64"):
    #     msgbox.alert(
    #         "For best performance, keep Roblox FPS locked at 60 FPS.\n\n"
    #         "Inside Roblox Settings: (Roblox icon in top left corner)\n"
    #         "   → set 'Maximum Frame Rate' to '60 FPS'\n"
    #         "   → set 'Graphics Mode' to 'Manual'\n" 
    #         "   → set 'Graphics Quality' to 'Low (levels 1–3)'\n"
    # 
    #         "Inside DIG: (cogwheel icon)\n"
    #         "   → enable 'Low Graphics' mode"
    #     )

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
        if macro.ui.open_config == True:
            restart_macro(["--open-config", "--skip-install"])
            pass
        elif macro.ui.restart_macro == True:
            restart_macro(["--skip-selection", "--skip-install"])
            pass
    
    logging.info("----------------- STOPPED ------------------")
    os.kill(os.getpid(), 9)