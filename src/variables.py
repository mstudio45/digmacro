import os
import time
import platform
import shutil
import random
import string
import subprocess
import collections

__all__ = ["Variables", "StaticVariables"]
current_os = platform.system()
compiled = "__compiled__" in globals()

# get compiled paths #
resource_path_str = ""
base_path_str = os.path.abspath(os.getcwd())

if compiled:
    try:
        from __nuitka_binary_dir import __nuitka_binary_dir # type: ignore
        resource_path_str = __nuitka_binary_dir
    except ImportError: pass

# fix paths #
if current_os == "Darwin" and ".app/Contents/MacOS" in __file__:
    base_path_str = os.path.abspath(os.path.join(__file__[:__file__.find(".app/") + len(".app")], ".."))

if resource_path_str.strip() == "": resource_path_str = os.path.dirname(os.path.abspath(__file__))

# path funcs #
def get_resource_path(*paths): return os.path.join(resource_path_str, *paths)
def get_base_path    (*paths): return os.path.join(base_path_str,     *paths)

# variables #
unix_open_app_cmd = next((cmd for cmd in ["open", "xdg-open", "gnome-open", "kde-open"] if shutil.which(cmd)), None)
where_cmd         = next((cmd for cmd in ["where", "which"] if shutil.which(cmd)), None)

class Variables:
    is_compiled = compiled
    is_running = True
    is_paused = True

    is_roblox_focused = True
    is_selecting_region = True

    # macro settings #
    session_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    current_version = "MATRIX.VERSION" if compiled else "2.0.4"
    current_branch = "MATRIX.BRANCH" if compiled else "dev"

    # minigame information #
    dig_count = 0
    click_count = 0
    rejoin_count = 0
    failed_minigame_attempts = 0
    failed_rejoin_attempts = 0
    
    money_region = { "left": 0, "top": 0, "height": 100, "width": 100 }
    minigame_region = { "left": 0, "top": 0, "height": 100, "width": 100 }
    last_minigame_detection = None

    money_information = collections.deque(maxlen=6)

    # macro states #
    is_minigame_active = False
    is_walking = False
    is_selling = False
    is_rejoining = False
    is_idle = lambda: (Variables.is_rejoining == False and Variables.is_walking == False and Variables.is_selling == False and Variables.is_minigame_active == False) == True

    # cmds #
    unix_open_app_cmd = unix_open_app_cmd
    where_cmd = where_cmd

    # functions #
    @staticmethod
    def sleep(duration, check_interval=0):
        start = time.time()
        
        while Variables.is_running:
            time.sleep(check_interval)
            if time.time() - start >= duration: break

        return Variables.is_running == False
    
    @staticmethod
    def open_link(url):
        if url is None: return

        try:
            if current_os == "Windows":
                import webbrowser
                webbrowser.open(url)
            else:
                subprocess.run([unix_open_app_cmd, url])
        except Exception as e:
            import logging
            logging.error(f"Failed to open link '{url}': {e}")

class StaticVariables:
    assets_folder                 = get_resource_path("assets")
    ui_filepath                   = os.path.join(assets_folder, "ui", "ui.html")
    guide_ui_filepath             = os.path.join(assets_folder, "ui", "guide.html")
    rose_pine_lib_path            = os.path.join(assets_folder, "rose-pine")

    storage_folder                = get_base_path("storage")
    # temp_folder                 = os.path.join(storage_folder, "temp")
    
    config_filepath               = os.path.join(storage_folder, "config.ini")
    region_filepath               = os.path.join(storage_folder, "region.json")
    pathfinding_macros_filepath   = os.path.join(storage_folder, "pathfinding_macros.json")
    discord_config_filepath       = os.path.join(storage_folder, "discord_settings.json")
    money_region_filepath         = os.path.join(storage_folder, "money_region.json")
    
    logs_folder                   = os.path.join(storage_folder, "logs")

    screenshots_folder            = os.path.join(storage_folder, "screenshots")
    prediction_screenshots_folder = os.path.join(screenshots_folder, "prediction", Variables.session_id)