# imports #
import os, sys, csv, time, traceback
import shutil, subprocess, importlib
import platform

current_os = platform.system() # Linux, Windows, Darwin
if current_os not in ["Linux", "Darwin", "Windows"]:
    print(f"Current OS '{current_os}' is not supported.")
    sys.exit(0)

compiled = "__compiled__" in globals()
def restart_macro():
    if compiled:
        executable_path = sys.executable
        os.execv(executable_path, [executable_path, "--skip-selection"])
    else:
        script_path = os.path.abspath(__file__)
        os.execv(sys.executable, [sys.executable, script_path, "--skip-selection"])
    return

# install requirements #
check_packages = True
installed_missing_packages = False

if check_packages:
    print("Checking packages...")
    # util functions #
    def get_distro(): # https://majornetwork.net/2019/11/get-linux-distribution-name-and-version-with-python/ #
        if current_os != "Linux": return "", ""

        RELEASE_DATA = {}
        
        with open("/etc/os-release") as f:
            reader = csv.reader(f, delimiter="=")
            for row in reader:
                if row: RELEASE_DATA[row[0]] = row[1]

        return RELEASE_DATA["ID"].lower(), RELEASE_DATA["NAME"]

    def get_linux_app_install_cmd(package_name):
        if distro_id in ["debian", "ubuntu", "raspbian", "linuxmint", "pop", "elementary", "zorin"]:
            return ["sudo", "apt-get", "install", "-y", package_name]
        elif distro_id in ["fedora"]:
            return ["sudo", "dnf", "install", "-y", package_name]
        elif distro_id in ["centos", "rhel", "redhat", "rocky", "almalinux", "oracle"]:
            return ["sudo", "yum", "install", "-y", package_name]
        elif distro_id in ["arch", "manjaro", "endeavouros", "garuda"]:
            return ["sudo", "pacman", "-S", "--noconfirm", package_name]
        elif distro_id in ["opensuse", "suse", "opensuse-leap", "opensuse-tumbleweed"]:
            return ["sudo", "zypper", "install", "-y", package_name]
        else:
            return f"Package install command not recognized for distro: {distro_name}"

    def get_linux_installed_packages():
        if distro_id in ["debian", "ubuntu", "raspbian", "linuxmint", "pop", "elementary", "zorin"]:
            cmd = ["dpkg-query", "-W", "-f=${Package}\n"]
        elif distro_id in ["fedora"]:
            cmd = ["dnf", "list", "installed"]
        elif distro_id in ["centos", "rhel", "redhat", "rocky", "almalinux", "oracle"]:
            cmd = ["yum", "list", "installed"]
        elif distro_id in ["arch", "manjaro", "endeavouros", "garuda"]:
            cmd = ["pacman", "-Qq"]
        elif distro_id in ["opensuse", "suse", "opensuse-leap", "opensuse-tumbleweed"]:
            cmd = ["zypper", "se", "-i"]
        else:
            return f"Unsupported distro for listing installed packages: {distro_name} ({distro_id})"
        
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            output = result.stdout.strip()
            packages = []

            if distro_id in ["debian", "ubuntu", "raspbian", "linuxmint", "pop", "elementary", "zorin"]:
                packages = output.split("\n")

            elif distro_id in ["fedora", "centos", "rhel", "redhat", "rocky", "almalinux", "oracle"]:
                lines = output.split("\n")
                packages = [line.split()[0] for line in lines if line and not line.startswith("Installed Packages")]

            elif distro_id in ["arch", "manjaro", "endeavouros", "garuda"]:
                packages = output.split("\n")

            elif distro_id in ["opensuse", "suse", "opensuse-leap", "opensuse-tumbleweed"]:
                lines = output.split("\n")
                for line in lines:
                    parts = line.split("|")
                    if len(parts) > 1 and parts[0].strip() == "i":
                        packages.append(parts[1].strip())

            return packages

        except Exception as e:
            print(f"Failed to list installed packages: {e}")
            return []
        
    # variables #
    distro_id, distro_name = get_distro()

    # command packages #
    shutil_applications = {
        "Linux": [
            "xdotool",
            "pkg-config"
        ]
    }
    def check_shutil_applications():
        if current_os not in shutil_applications: return

        missing_applications = []
        for cmd in shutil_applications[current_os]:
            if shutil.which(cmd) is not None: continue
            missing_applications.append(cmd)

        if len(missing_applications) == 0: 
            print("[check_shutil_applications] All required applications are installed.")
            return

        if current_os == "Linux":
            for missing_application in missing_applications:
                install_cmd = get_linux_app_install_cmd(missing_application)
                if isinstance(install_cmd, str):
                    print(install_cmd)
                    sys.exit(1)

                try: 
                    print(f"[check_shutil_applications] Installing application: {missing_application} using {install_cmd}")
                    subprocess.check_call(install_cmd)
                except Exception as e:
                    print(f"[check_shutil_applications] Failed to install '{missing_application}' requirement: \n{traceback.format_exc()}")
                    sys.exit(1)
                installed_missing_packages = True
            
            print("[check_shutil_applications] Done.")

    check_shutil_applications()

    # apt packages #
    apt_packages = {
        "Linux": {
            "gcc"
        }
    }
    def check_apt_packages():
        if current_os not in apt_packages: return

        installed_packages = get_linux_installed_packages()
        if isinstance(installed_packages, str):
            print(installed_packages)
            sys.exit(1)

        missing_packages = []
        for package in apt_packages[current_os]:
            if package in installed_packages: continue
            missing_packages.append(package)

        if len(missing_packages) == 0: 
            print("[check_apt_packages] All required system packages are installed.")
            return
        
        if current_os == "Linux":
            for missing_package in missing_packages:
                install_cmd = get_linux_app_install_cmd(missing_package)
                if isinstance(install_cmd, str):
                    print(install_cmd)
                    sys.exit(1)

                try:
                    print(f"[check_apt_packages] Installing system package: {missing_package} using {install_cmd}")
                    subprocess.check_call(install_cmd)
                except Exception as e:
                    print(f"[check_apt_packages] Failed to install '{missing_package}' requirement: \n{traceback.format_exc()}")
                    sys.exit(1)
                installed_missing_packages = True
            
            print("[check_apt_packages] Done.")

    check_apt_packages()

    # python packages #
    if compiled == False:
        def install_package(pip_name):
            try: 
                print(f"[install_package] Installing python package: {pip_name}")
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
            except Exception as e:
                print(f"[install_package] Failed to install '{pip_name}' requirement: \n{traceback.format_exc()}")
                sys.exit(1)
        
        required_packages = {
            "all": {
                # finder libs #
                "opencv-python": "cv2",
                "numpy": "numpy",
                "PyAutoGUI": "pyautogui",
                "mss": "mss",
                "screeninfo": "screeninfo",

                # input libs #
                "pynput": "pynput",

                # updater libs #
                "requests": "requests",

                # ui libs #
                "PySide6": "PySide6",

                # misc libs #
                "psutil": "psutil",
                "logging": "logging",
                "pillow": "PIL"
            },

            "Windows": {
                # ui #
                "pywebview": "webview",

                # screenshot lib #
                "bettercam": "bettercam",

                # win32 api #
                "PyGetWindow": "pygetwindow",
                "pywin32": "win32gui",

                # input libs #
                "PyAutoIt": "autoit"
            },

            "Linux": {
                "pywebview[gtk]": "webview",
            },

            "Darwin": {
                "pywebview": "webview",
                "PyObjC": "AppKit"
            }
        }
        check_import_only = ["pywebview[gtk]"]

        def check_packages():
            # get installed packages #
            reqs = subprocess.check_output([sys.executable, "-m", "pip", "freeze"])
            installed_packages = [r.decode().split("==")[0] for r in reqs.split()]
            missing_packages = []
            
            # check all packages #
            for os, required_obj in required_packages.items():
                if not (os == "all" or os == current_os): continue

                for pip_name, _package in required_obj.items():
                    if pip_name in check_import_only or pip_name in installed_packages: continue
                    if pip_name not in missing_packages: missing_packages.append(pip_name)
            
            # check importerrors #
            for os, required_obj in required_packages.items():
                if not (os == "all" or os == current_os): continue

                for pip_name, package in required_obj.items():
                    try: importlib.import_module(package)
                    except ImportError as e:
                        if pip_name not in missing_packages: missing_packages.append(pip_name)

            # install packages #
            if len(missing_packages) == 0: 
                print("[check_packages] All required packages are installed.")
                return

            print(f"Missing packages detected: {missing_packages}")
            if compiled:
                print(f"Missing packages detected, please install them manually: {missing_packages}")
                sys.exit(1)

            installed_missing_packages = True
            for pip_name in missing_packages:
                install_package(pip_name)

            print("[check_packages] Done.")

        check_packages()

    # special errors #
    def check_special_errors(import_error=False):
        # check tkinter tcl issues #
        import tkinter as tk
        try:
            root = tk.Tk()
            root.withdraw()
            root.destroy()
        except (tk.TclError, ImportError) as e:
            if isinstance(e, ImportError):
                if import_error == True:
                    print(f"[check_special_errors] Failed to properly install tkinter: {str(e)}")
                    sys.exit(1)
                else:
                    installed_missing_packages = True
                    install_package("tk")
                    return check_special_errors(import_error=True) # restart again
            
            err_ = "Please setup the 'TCL_LIBRARY' and 'TK_LIBRARY' env variables manually and try again."
            if current_os != "Windows":
                print(err_)
                sys.exit(1)

            python_ver = platform.python_version()
            valid_python_path, valid_python_exe = "", ""

            paths_result = subprocess.run(["where", "python"], capture_output=True, text=True, check=True)
            paths = [line.strip() for line in paths_result.stdout.split("\n") if line.strip()]

            for path in paths:
                if path == sys.executable: continue

                version_result = subprocess.run([path, "--version"], capture_output=True, text=True)
                version_output = version_result.stdout.strip() or version_result.stderr.strip()

                if version_output.endswith(python_ver):
                    valid_python_exe, valid_python_path = path, os.path.dirname(path)
                    break
            
            if valid_python_path == "" or valid_python_exe == "":
                print(f"[check_special_errors] Failed to find the valid python path. {err_}")
                sys.exit(1)

            # get tcl version from exe #
            tcl_version_result = subprocess.run([valid_python_exe, "-c", "import tkinter; print(tkinter.TclVersion)"], capture_output=True, text=True)
            tcl_version_output = tcl_version_result.stdout.strip() or tcl_version_result.stderr.strip()

            tcl_path = os.path.join(valid_python_path, "tcl", "tcl" + str(tcl_version_output))
            tk_path = os.path.join(valid_python_path, "tcl", "tk" + str(tcl_version_output))

            if os.path.isdir(tcl_path) == False or os.path.isdir(tk_path) == False:
                print(f"[check_special_errors] Failed to find the valid tcl/tk path. {err_}")
                sys.exit(1)

            os.environ["TCL_LIBRARY"] = tcl_path
            os.environ["TK_LIBRARY"]  = tk_path
        except Exception as e:
            print(f"[check_special_errors] Failed to properly test tkinter.")

        print("[check_special_errors] Done.")

    check_special_errors()

    print("------------------ INSTALLED --------------------")
    if installed_missing_packages == True: restart_macro()

# imports #
import logging
import threading
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

    print("Creating screenshot folders...")
    FileHandler.create_folder(StaticVariables.prediction_screenshots_path)

    print("Loading config...")
    Config.load_config() # default_config_loaded
    Config.WINDOW_NAME = Config.WINDOW_NAME + " | " + Variables.session_id 

    from utils.logs import setup_logger;
    print("Loading logger...")
    setup_logger()

    ## check version ##
    current_version = "2.0.0"
    current_branch = "beta"

    try:
        logging.info("Checking current version...")

        import requests, json
        req = requests.get("https://raw.githubusercontent.com/mstudio45/digmacro/refs/heads/storage/versions.json")
        versions = json.loads(req.text)

        # check versions #
        if current_branch not in versions: raise Exception(f"{current_branch} is not an valid branch.")
        if versions[current_branch] != current_version:
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
        msgbox.alert(f"Failed to check for new updates. {traceback.format_exc()}")

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
        
        elif res == "Exit": os.kill(os.getpid(), 9)
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
            self.sct = mss.mss()

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
                    self.update_window_status("Error", f"Failed to start the minigame in the second try, waiting...", "red")
                    time.sleep(2.5)
                    return
                
                self.update_window_status("Error", f"Failed to start the minigame!", "red")

                logging.info("Equipping shovel...")
                press_key("+") # equip the shovel #
                time.sleep(0.5)
                return self.start_minigame(equipped=True)


        def main_loop(self, _):
            sct = mss.mss()

            while Variables.is_running:
                time.sleep(0.25)

                # handle idle_time, and skip if not in idle #
                if not Variables.is_idle():
                    if Variables.is_minigame_active:
                        self.update_window_status("Minigame", f"Completing minigame...", "green")
                    
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
                    self.update_window_status("Minigame", f"Waiting for minigame...", "yellow")

                    # pathfinding handler #
                    was_last_key = False
                    if Config.PATHFINDING == True:
                        self.update_window_status("Pathfinding", f"Walking to the next point...", "green")
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

                    while not self._stop_event.is_set():
                        frame_start = time.perf_counter()
                        
                        # update state and click #
                        finder.update_state(sct)
                        finder.handle_click()
                        
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
            self.sct.close()

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
            if FileHandler.is_folder_empty(StaticVariables.prediction_screenshots_path):
                FileHandler.try_delete_folder(StaticVariables.prediction_screenshots_path)

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