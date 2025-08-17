# imports #
import os
import sys
import time
import traceback
import subprocess
import platform

current_os = platform.system() # Linux, Windows, Darwin
if current_os not in ["Linux", "Darwin", "Windows"]:
    print(f"Current OS '{current_os}' is not supported.")
    sys.exit(0)

# restart macro handler #
def get_launcher_path():
    for arg in sys.argv:
        if arg.startswith("--from-launcher="):
            return arg.split("=", 1)[1]
    return None

def get_working_dir():
    for arg in sys.argv:
        if arg.startswith("--cwd="):
            return arg.split("=", 1)[1]
    return None

def restart_macro(args=["--skip-selection"]):
    cwd, binary, arguments = os.getcwd(), "", []

    launcher_path = get_launcher_path()  
    if launcher_path:
        binary = launcher_path
        arguments = [launcher_path] + args
        cwd = os.path.dirname(os.path.abspath(launcher_path))
    else:
        if current_os == "Darwin":
            binary = sys.argv[0]
            arguments = args
        else:
            binary = os.path.abspath(sys.executable)
            arguments = [binary, os.path.abspath(__file__)] + args

    # log the command #
    log_info = (
        f"=== Restart Requested ===\n"
        f"Sys Executable: {sys.executable}\n"

        f"Original CWD: {os.getcwd()}\n"
        f"Restart CWD: {cwd}\n"

        f"Binary Path: {binary}\n"
        f"Arguments: {' '.join(map(str, arguments))}\n"
        f"=========================\n"
    )

    try: import logging; logging.info(log_info)
    except Exception: print(log_info)

    # restart macro #
    # if cwd is not None: os.chdir(cwd)
    # os.execv(binary, arguments)

    subprocess.Popen(arguments, cwd=cwd)
    sys.exit(0)

# install requirements #
from utils.packages.distro_variables import log_install, start_log_file, close_log_file, current_arch
from utils.packages.check_apt import check_apt_packages
from utils.packages.check_errors import check_special_errors
from utils.packages.check_python import check_pip_packages
from utils.packages.check_shutil import check_shutil_applications
from utils.packages.versions import is_version_outdated

if "--skip-install" not in sys.argv:
    start_log_file()
    log_install(f"[INFO] Detected OS: {current_os} ({current_arch})")

    if "--only-install" in sys.argv:
        log_install("Only installing packages...")

        check_shutil_applications()
        check_apt_packages()
        check_pip_packages()

        close_log_file()
        sys.exit(0)

    if check_shutil_applications() or check_apt_packages() or check_pip_packages():
        close_log_file()

        restart_macro(["--skip-install"])
        sys.exit(0)

check_special_errors() # still required to run, fixes for tkinter on windows #
close_log_file()

# load config and logging #
from variables import Variables, StaticVariables
from config import Config

from utils.logs import setup_logger, disable_spammy_loggers
import utils.general.filehandler as FileHandler

# create folders (on macOS it will prompt an allow 'folder' access notification) #
FileHandler.create_folder(StaticVariables.storage_folder)
FileHandler.create_folder(StaticVariables.logs_folder)
# FileHandler.create_folder(StaticVariables.temp_folder)

Config.load_config() # default_config_loaded
setup_logger()

import logging
import threading
import mss
import numpy as np
import cv2
import json

import interface.msgbox as msgbox

# anti-crash error logger #
logging.info("Loading Crash Handler...")
def log_uncaught_exceptions(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    msgbox.alert(f"Uncaught Exception found. Logs are saved at: {StaticVariables.log_filepath}\n\n" + error_message, log_level=logging.ERROR)

    # disable logging #
    try:
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
    except: pass

    time.sleep(0.1)

    # rename the log file #
    try: FileHandler.rename(StaticVariables.log_filepath, StaticVariables.crash_log_filepath)
    except: pass

    sys.exit(0)

sys.excepthook = log_uncaught_exceptions

# main thread #
if __name__ == "__main__":
    cwdir = get_working_dir()
    if cwdir is not None:
        os.chdir(cwdir)
        if cwdir not in sys.path: sys.path.insert(0, cwdir)

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

    # macOS Permission Checks (original by SalValichu) #
    """
    if current_os == "Darwin":
        try:
            logging.info("[macOS Permissions] Checking permissions...")
            permission_urls = {
                "Accessibility": "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
                "Input Monitoring": "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent",
                "Screen Recording": "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
            }

            def create_permission_message(permission_type, reason):
                app_name = f"digmacro_macos_{current_arch}"
                message = f\"""This application requires '{permission_type}' permission to {reason}.

Please go to: System Settings → Privacy & Security → {permission_type}
Then, ensure this application ({app_name}) is enabled.

⚠ If you are opening the macro with Terminal (or any other application), ensure that application also has '{permission_type}' permission enabled. ⚠

Press 'OK' after enabling '{permission_type}' permission, the macro will restart itself.
If the permission is enabled and you are still being prompted with this notification, press 'Skip'.""\"
            
                return message

            def open_system_preferences(permission_type):
                try:
                    url = permission_urls.get(permission_type, "x-apple.systempreferences:com.apple.preference.security")
                    subprocess.run(["open", url], check=True)
                    return True

                except Exception as e:
                    logging.error(f"Failed to open System Preferences: {e}")
                    return False

            def check_accessibility_permission():
                try:
                    from ApplicationServices import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt # type: ignore
                    options = {kAXTrustedCheckOptionPrompt: False}
                    return AXIsProcessTrustedWithOptions(options), ""

                except ImportError as e:
                    return False, f"Could not import ApplicationServices: {e}"
                    
                except Exception as e:
                    return False, f"Accessibility check failed: {e}"

            def check_input_monitoring_permission():
                try:
                    import ctypes
                    from ctypes import cdll
    
                    iokit = cdll.LoadLibrary('/System/Library/Frameworks/IOKit.framework/IOKit')
                    kIOHIDRequestTypeListenEvent = 1
                    kIOHIDAccessTypeGranted = 0

                    result = iokit.IOHIDCheckAccess(kIOHIDRequestTypeListenEvent)
                    has_permission = (result == kIOHIDAccessTypeGranted)
                    return has_permission, ""

                except ImportError as e:
                    return False, f"Could not import ctypes: {e}"
                    
                except Exception as e:
                    return False, f"Input Monitoring check failed: {e}"

            def check_screen_recording_permission():
                try:
                    from Quartz import CGPreflightScreenCaptureAccess, CGMainDisplayID # type: ignore
                    from Quartz import CGDisplayStreamCreateWithDispatchQueue # type: ignore
                    import dispatch # type: ignore
                    
                    if CGPreflightScreenCaptureAccess(): return True, ""
                    
                    # Fallback check #
                    try:
                        def stream_callback(status, timestamp, frame, update_ref): 
                            pass
                        
                        display_id = CGMainDisplayID()
                        main_queue = dispatch.dispatch_get_main_queue()
                        stream_ref = CGDisplayStreamCreateWithDispatchQueue(
                            display_id, 1, 1, 1111970369, None, main_queue, stream_callback
                        )
                        
                        has_permission = (stream_ref is not None)
                        return has_permission, ""
                        
                    except Exception as fallback_error:
                        return False, f"Screen Recording fallback check failed: {fallback_error}"
                        
                except ImportError as e:
                    return False, f"Could not import Quartz: {e}"
                    
                except Exception as e:
                    return False, f"Screen Recording check failed: {e}"

            # Check Accessibility #
            has_accessibility, accessibility_error = check_accessibility_permission()
            if not has_accessibility:
                logging.warning(f"[macOS Permissions] Accessibility disabled: {accessibility_error}")
                open_system_preferences("Accessibility")
                
                message = create_permission_message("Accessibility", "control mouse and keyboard")
                res = msgbox.confirm(message, title="DIGMacro - Permission Issue", buttons=("OK", "Skip", "Exit"))
                if res == "OK":
                    restart_macro(["--skip-install"])
                    sys.exit(0)
                elif res == "Skip":
                    logging.info("[macOS Permissions] Accessibility permission skipped")
                else:
                    sys.exit(0)
            else: logging.info("[macOS Permissions] Accessibility access is enabled.")

            # Check Input Monitoring #
            has_input_monitoring, input_error = check_input_monitoring_permission()
            if not has_input_monitoring:
                logging.warning(f"[macOS Permissions] Input Monitoring disabled: {input_error}")
                open_system_preferences("Input Monitoring")
                
                message = create_permission_message("Input Monitoring", "allow global hotkeys")
                res = msgbox.confirm(message, title="DIGMacro - Permission Issue", buttons=("OK", "Skip", "Exit"))
                if res == "OK":
                    restart_macro(["--skip-install"])
                    sys.exit(0) 
                elif res == "Skip":
                    logging.info("[macOS Permissions] Input Monitoring permission skipped")
                else:
                    sys.exit(0)
            else: logging.info("[macOS Permissions] Input Monitoring access is enabled.")

            # Check Screen Recording #
            has_screen_recording, screen_error = check_screen_recording_permission()
            if not has_screen_recording:
                logging.warning(f"[macOS Permissions] Screen Recording disabled: {screen_error}")
                open_system_preferences("Screen Recording")

                message = create_permission_message("Screen Recording", "detect the minigame")
                res = msgbox.confirm(message, title="DIGMacro - Permission Issue", buttons=("OK", "Skip", "Exit"))
                if res == "OK":
                    restart_macro(["--skip-install"])
                    sys.exit(0)
                elif res == "Skip":
                    logging.info("[macOS Permissions] Screen Recording permission skipped")
                else:
                    sys.exit(0)
            else: logging.info("[macOS Permissions] Screen Recording access is enabled.")

        except ImportError as e:
            logging.warning(f"[macOS Permissions] Could not import required packages: {e}")

        except Exception as e:
            logging.error(f"[macOS Permissions] Error during permission check: {e}")
    """
        
    ##########################################################################################################################

    logging.info("Loading screen information...")
    from utils.images.screenshots import screenshot_cleanup
    from utils.images.screen import screen_res_str, screen_region

    ## check version ##
    try:
        if Variables.current_version == "MATRIX.VERSION" or Variables.current_branch == "MATRIX.BRANCH":
            logging.info("Current version is not set, skipping version check.")
        else:
            logging.info("Checking current version...")

            import requests
            req = requests.get("https://raw.githubusercontent.com/mstudio45/digmacro/refs/heads/storage/versions.json", timeout=2.5)
            versions = json.loads(req.text)

            # check versions #
            if Variables.current_branch not in versions: raise Exception(f"{Variables.current_branch} is not an valid branch.")
            latest_branch_version = versions[Variables.current_branch]
            is_outdated = is_version_outdated(Variables.current_version, latest_branch_version)

            logging.info(f"Running on '{Variables.current_branch}' - {Variables.current_version} | Latest '{Variables.current_branch}' version: {latest_branch_version} | {Variables.current_version} < {latest_branch_version} = {is_outdated}")
            if is_outdated:
                confirm, autoupdate = "No", False
                if Variables.launcher_path is None:
                    confirm = msgbox.confirm((
                        f"A new version is avalaible at https://github.com/mstudio45/digmacro!\n{Variables.current_version} > {latest_branch_version}\n"
                        "Do you want to open the GitHub page?\n\n" 
                        "[ If you don't want to update, don't encounter any issues don't report them - you are using an outdated version. ] "
                    ))
                else:
                    confirm = msgbox.confirm((
                        f"A new version is avalaible at https://github.com/mstudio45/digmacro!\n{Variables.current_version} > {latest_branch_version}\n"
                        "Do you want to update the macro automatically?\n\n" 
                        "[ If you don't want to update, don't encounter any issues don't report them - you are using an outdated version. ] "
                    ))
                    autoupdate = True

                if confirm == "Yes":
                    if autoupdate:
                        subprocess.Popen([Variables.launcher_path, "--update-source"], cwd=os.path.dirname(os.path.abspath(Variables.launcher_path)))
                        sys.exit(0)
                    else:
                        Variables.open_link(f"https://github.com/mstudio45/digmacro/releases/tag/v{latest_branch_version}")

    except Exception as e:
        msgbox.alert(f"Failed to check for new updates. {str(e)}")

    ##########################################################################################################################
    def start_config():
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
        if config_ui.start_macro_now == True: restart_macro(["--skip-install", "--skip-selection"])
        else:                                 sys.exit(0)

    if "--skip-selection" in sys.argv or "--region-check" in sys.argv:
        logging.info("Skipping config/start selection.")
    else:
        # run config #
        if "--open-config" in sys.argv:
            start_config()
        else:
            res = msgbox.confirm("What would you like to do?", buttons=("Start Macro", "Edit the configuration", "Exit"))
            if res == "Edit the configuration": start_config()
            elif res == "Exit" or res == "":    sys.exit(0)
            else:                               logging.info("Starting the macro...")
    ##########################################################################################################################

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
    
    logging.info("===============================")

    # main loader #
    logging.info("Importing libraries...")

    logging.info("======== INPUT HANDLERS ========".center(60, "="))
    from utils.input.mouse import left_click, move_mouse
    from utils.input.keyboard import press_key, setup_global_hotkeys
    logging.info("======== INPUT HANDLERS END ========".center(60, "="))

    logging.info("======== DETECTORS HANDLER ========".center(60, "="))
    from utils.detectors.handler import MainHandler
    from utils.general.fps_counter import FPSCounter
    logging.info("======== DETECTORS HANDLER END ========".center(60, "="))

    logging.info("======== AUTOMATIZATION HANDLERS ========".center(60, "="))
    from utils.sellinv import SellUI
    from utils.pathfinding import PathfingingHandler
    logging.info("======== AUTOMATIZATION HANDLERS END ========".center(60, "="))

    logging.info("======== ROBLOX HANDLERS ========".center(60, "="))
    from utils.roblox.rejoin import roblox_status_handler, rejoin_dig, can_rejoin
    from utils.roblox.window import is_roblox_focused
    logging.info("======== ROBLOX HANDLERS END ========".center(60, "="))

    logging.info("======== INTERFACE HANDLERS ========".center(60, "="))
    import interface.web_ui as WebUI
    from interface.region_selection import RegionSelector
    logging.info("======== INTERFACE HANDLERS END ========".center(60, "="))

    logging.info("======== DISCORD BOT ========".center(60, "="))
    from utils.discord.bot import discord_bot
    logging.info("======== DISCORD BOT END ========".center(60, "="))

    ###########################################################################################

    memory_handler = None
    if Config.GLOBAL_DETECTION_METHOD == "Memory":
        logging.info("Loading Memory handler...")
        from utils.detectors.roblox_memory.main import MemoryHandler
        memory_handler = MemoryHandler()

    logging.info("Loading MacroHandler...")
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
            self.region_selector = None
            
            if Config.GLOBAL_DETECTION_METHOD == "Memory":
                self.finder = MainHandler(memory_handler)
            else:
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

            if not os.path.isfile(StaticVariables.region_filepath):
                logging.info("storage/region.json file doesn't exist.")
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
            Variables.is_selecting_region = True
            
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
                if current_os == "Darwin":
                    from PySide6.QtWidgets import QApplication
                    q_app = QApplication(sys.argv)
                    
                    self.region_selector = RegionSelector(stop_macro=True)
                    self.region_selector.start()

                    q_app.exec()
                else:
                    self.region_selector = RegionSelector(stop_macro=True)
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
                
                FileHandler.write(StaticVariables.region_filepath, json.dumps(self.saved_regions, indent=4))
                logging.info(f"Region saved successfully as {self.region_key}.")
                logging.info(f"Region '{self.region_key}' selected successfully.")

                if current_os == "Darwin":
                    self.exit_macro()
                    restart_macro(["--skip-selection", "--skip-install"])
                    return

            # region selected correctly #
            logging.info("Region has been loaded successfully.\n")
            Variables.is_roblox_focused = False
            Variables.is_selecting_region = False
            Variables.minigame_region = region
            self.finder.setup_region_image_size()
            logging.info("Setup region has finished.")

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
            self.update_window_status("Starting minigame...", f"Total dig count: {Variables.dig_count:,}", "green")

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
            FileHandler.create_folder(StaticVariables.prediction_screenshots_folder)

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
                    if Config.ENABLE_AUTO_REJOIN:
                        if Variables.is_rejoining: continue

                        if can_rejoin(self.total_idle_time):
                            self.update_window_status("Rejoining...", "Waiting for Roblox to load...", "yellow")

                            self.total_idle_time = 0
                            rejoin_dig()
                            continue

                    if memory_handler is not None:
                        if memory_handler.loaded == False:
                            self.update_window_status("Waiting", "Waiting for Memory Handler to initialize...", "orange")
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
                        if last_interact > 0 and (time.time() - last_interact) >= 1.75:
                            Variables.dig_count = Variables.dig_count + 1
                            Variables.last_minigame_detection = None

                            logging.info("========== Added 1 to dig_count, waiting... ===========")
                            digging_finished = True

                            if discord_bot.running:
                                try:
                                    if Variables.dig_count > 0 and Variables.dig_count % Config.DISCORD_MINIGAME_INFO_FREQUENCY == 0:
                                        logging.info("[Discord] Sending minigame information.")
                                        discord_bot.send_minigame_info()
                                except Exception as e:
                                    logging.warning(f"[Discord] Failed to send minigame information: {str(e)}")
                                
                                threading.Thread(target=discord_bot.check_new_item, daemon=True).start()
                            else:
                                if Variables.sleep(0.75): break
                    
                    else: digging_finished = True

                    # skip if digging didnt finish #
                    if not digging_finished: continue

                    self.finder.debug_img = None
                    self.total_idle_time = self.total_idle_time + 0.1

                    # no dirt bar #
                    if Variables.is_minigame_active == False:
                        self.update_window_status("Minigame", "Waiting for minigame to be detected...", "yellow")

                    elif self.finder.DirtBar.clickable_position is None:
                        self.update_window_status("Minigame", "Waiting for dirt bar...", "yellow")

                    elif self.finder.PlayerBar.current_position is None:
                        self.update_window_status("Minigame", "Waiting for player bar...", "yellow")

                    else:
                        self.update_window_status("Minigame", "Waiting for minigame...", "yellow")

                    # auto sell #
                    if Config.ENABLE_AUTO_SELL == True: self.sell_all_items()

                    # pathfinding handler #
                    if Config.ENABLE_PATHFINDING == True:
                        self.update_window_status("Pathfinding", "Walking to the next point...", "green")   

                        if self.pathfinding.current_macro == "risk_spin":
                            if self.risk_spin_tuple is None:
                                self.risk_spin_tuple = (screen_region["width"] // 2, screen_region["height"] // 2, 100 * (screen_region["width"] / 1280))
                                # 100 pixel is only for 2560x1440 so get scale factor for that #

                            middle_x, middle_y, offset = self.risk_spin_tuple

                            move_mouse(middle_x, middle_y, steps=1)
                            threading.Thread(target=move_mouse, args=(middle_x + offset, middle_y, 13, 0.0125, ), daemon=True).start()
                            for i in range(1, 10):
                                left_click()
                                time.sleep(0)
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
            logging.info("Setting up finder threads...")
            
            class FinderThread(threading.Thread):
                def __init__(self, finder, target_fps):
                    super().__init__()
                    self.finder = finder
                    self.frame_time = 1 / target_fps
                    
                    self.daemon = True
                    self._stop_event = threading.Event()

                    logging.info(f"Finder thread created with target FPS: {target_fps} (frame time: {self.frame_time:.4f}s)")

                if memory_handler is not None:
                    def run(self):
                        logging.info(f"Finder loop starting...")
                        finder = self.finder

                        while not self._stop_event.is_set():
                            if finder.update_state():
                                finder.handle_click()
                            time.sleep(0)

                        logging.info(f"Finder loop stopped successfully.")
                else:
                    def run(self):
                        logging.info(f"Finder loop starting...")

                        sct = mss.mss()
                        fps_counter = FPSCounter()

                        frame_time = self.frame_time
                        finder = self.finder

                        while not self._stop_event.is_set():
                            frame_start = time.perf_counter()

                            # update state and click #
                            if finder.update_state(sct):
                                finder.handle_click()

                            # update fps #
                            fps_counter.accumulate_frame_time(frame_start)
                            finder.current_fps = fps_counter.get_fps()
                            
                            # force target fps #
                            elapsed = time.perf_counter() - frame_start
                            sleep_time = max(0, frame_time - elapsed)
                            if sleep_time > 0: time.sleep(sleep_time)

                        del fps_counter
                        del sct
                        logging.info(f"Finder loop stopped successfully.")

                def stop(self):
                    self._stop_event.set()

            # create finder threads #
            thread = FinderThread(self.finder, Config.TARGET_FPS)
            self.add_thread("finder_thread", thread=thread)
            thread.start()

        def setup_roblox_focused_thread(self):
            if not Variables.is_running: return
            logging.info("Loading Roblox Focus thread...")
            
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
            logging.info("Starting Roblox Focus thread...")
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
            for (folderpath, is_empty) in FileHandler.get_folders(StaticVariables.screenshots_folder):
                if is_empty == True: FileHandler.try_delete_folder(folderpath)

            logging.info("----------- CLEANUP DONE -------------")

    # load main macro handler #
    logging.info("Initializing MacroHandler...")
    macro = MacroHandler()

    # check config values #
    validation_rules = {
        "ENABLE_DISCORD_BOT": {
            "GENERAL": {
                "Invalid Bot Token": Config.DISCORD_BOT_TOKEN == "",
                "Invalid User ID": Config.DISCORD_USER_ID == "" or not isinstance(Config.DISCORD_USER_ID, int),
            },

            "DISCORD_ENABLE_STATISTICS": {
                "Invalid Money Region selected for Statistics": Config.DISCORD_MONEY_LABEL_REGION == None or Config.DISCORD_MONEY_LABEL_REGION == (0,0,0,0)
            }
        },

        "ENABLE_AUTO_SELL": {
            "GENERAL": {
                "Invalid button position selected": Config.AUTO_SELL_MODE == "Mouse Movement" and Config.AUTO_SELL_BUTTON_POSITION == (0, 0),
            }
        },

        "ENABLE_PATHFINDING": {
            "GENERAL": {
                "Macro 'risk_spin' only works on Windows": current_os != "Windows" and Config.PATHFINDING_MACRO == "risk_spin",
                "Macro 'risk_spin' requires 'AUTO_START_MINIGAME'": Config.AUTO_START_MINIGAME == False and Config.PATHFINDING_MACRO == "risk_spin"
            }
        }
    }

    for config_name, config_rules in validation_rules.items():
        if not Config[config_name]:
            logging.info(f"Skipping config validation for '{config_name}' since it's disabled.")
            continue

        # check required setting #
        general_checks = config_rules.get("GENERAL", {})
        for warning_message, condition_is_met in general_checks.items():
            if condition_is_met:
                msgbox.alert(f"{warning_message}. '{config_name}' has been disabled.", log_level=logging.WARNING)
                setattr(Config, config_name, False)
                break
        
        if not Config[config_name]: continue

        # check specific sub setting #
        for sub_config_name, sub_config_rules in config_rules.items():
            if sub_config_name == "GENERAL": continue

            if not Config[sub_config_name]:
                logging.info(f"Skipping config validation for '[{config_name}] {sub_config_name}' since it's disabled.")
                continue

            for warning_message, condition_is_met in sub_config_rules.items():
                if condition_is_met:
                    msgbox.alert(f"{warning_message}. '[{config_name}] {sub_config_name}' has been disabled.", log_level=logging.WARNING)
                    setattr(Config, sub_config_name, False)
                    break

    # required code changes #
    if Config.ENABLE_AUTO_SELL == True and Config.AUTO_SELL_AFTER_PATHFINDING_MACRO == True and Config.ENABLE_PATHFINDING == True:
        if Config.PATHFINDING_MACRO != "risk_spin" and Config.PATHFINDING_MACRO in Config.PathfindingMacros:
            Config.AUTO_SELL_REQUIRED_ITEMS = len(Config.PathfindingMacros[Config.PATHFINDING_MACRO]) + 1
            logging.info(f"Auto Sell (After Pathfinding) enabled, will sell after: {Config.AUTO_SELL_REQUIRED_ITEMS} items (amount of keys + 1)")

    if Config.ENABLE_PATHFINDING == True and Config.PATHFINDING_MACRO == "risk_spin":
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
                Config.ENABLE_PATHFINDING = False
            else:
                logging.info("Mouse Acceleration/Enhance disabled.")
        else:
            msgbox.alert("Pathfinding macro 'risk_spin' only works on Windows. Pathfinding has been disabled.")
            Config.ENABLE_PATHFINDING = False

    # region #
    macro.setup_finder_thread()
    if Config.GLOBAL_DETECTION_METHOD == "Memory":
        logging.info("Region skipped; Using Memory handler...")
    else:
        msgbox.alert("The macro currently can't complete Divine, Prismatic and Secret items due to the recent DIG update. (With the OpenCV method)")
        macro.setup_region_setter()

    # run threads #
    macro.setup_roblox_focused_thread()

    # setup hotkeys #
    macro.setup_hotkeys()

    # load ui #
    if Variables.is_running:
        logging.info("Disabling spammy loggers...")
        disable_spammy_loggers()

        # load discord bot #
        if Config.ENABLE_DISCORD_BOT == True:
            if Config.DISCORD_ENABLE_STATISTICS:
                if memory_handler is not None:
                    logging.info("[Discord] Loading Stats modules...")
                    from utils.detectors.gamestats.memory import GameOCR
                    discord_bot.ocr_util = GameOCR(memory_handler)
                else:
                    logging.info("[Discord] Loading OCR and Stats modules...")
                    from utils.detectors.gamestats.ocr import GameOCR
                    discord_bot.ocr_util = GameOCR()

                from utils.detectors.stat_lib import GameStatLib
                discord_bot.stat_lib = GameStatLib(discord_bot)
            
            discord_bot.run()
        else:
            logging.info("Discord Bot is disabled.")

        # load ui #
        if memory_handler is not None:
            logging.info("Loading Memory Module...")
            def handler_for_memory():
                memory_handler.reload_roblox_memory()
                while Variables.is_running:
                    if Variables.sleep(1): break
                    if roblox_status_handler.playing: continue

                    memory_handler.clear_everything()

                    logging.info("Waiting for User to join DIG...")
                    while roblox_status_handler.playing == False:
                        if Variables.sleep(1): break
                    
                    memory_handler.reload_roblox_memory()
                logging.info("Memory Handler loop stopped.")
            threading.Thread(target=handler_for_memory, daemon=True).start()

        logging.info("Loading UI...")
        macro.ui.start(macro.main_loop)

        logging.info("UI Closed, starting cleanup...")

        if discord_bot.running:
            logging.info("[Discord] Stopping Discord Bot...")
            discord_bot.stop()
        
        if discord_bot.stat_lib:
            logging.info("Stopping Stats Module..")
            discord_bot.stat_lib.stat_util.stop()
        
        logging.info("Cleaning Macro Handler...")
        macro.exit_macro()

        if macro.ui.open_config == True:
            restart_macro(["--open-config", "--skip-install"])
            pass
        elif macro.ui.restart_macro == True:
            restart_macro(["--skip-selection", "--skip-install"])
            pass
    
    logging.info("----------------- STOPPED ------------------")
    os.kill(os.getpid(), 9)