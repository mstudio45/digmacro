import os
import sys
import time
import platform
import shutil
import random
import string
import collections
import logging
import webbrowser

__all__ = ["Variables", "StaticVariables"]
current_os = platform.system()
def get_launcher_path():
    for arg in sys.argv:
        if arg.startswith("--from-launcher="):
            return arg.split("=", 1)[1]
    return None

launcher_path = get_launcher_path()
is_from_launcher = launcher_path is not None

# get paths #
resource_path_str = os.path.dirname(os.path.abspath(__file__))
base_path_str = ""

if is_from_launcher: 
    if ".app/Contents" in launcher_path:
        app_bundle_path = launcher_path.split(".app/")[0] + ".app"
        base_path_str = os.path.dirname(os.path.abspath(app_bundle_path))
    else:
        base_path_str = os.path.dirname(os.path.abspath(launcher_path))
else:
    base_path_str = os.path.abspath(os.getcwd())

# path funcs #
def get_resource_path(*paths): return os.path.join(resource_path_str, *paths)
def get_base_path    (*paths): return os.path.join(base_path_str,     *paths)

# variables #
unix_open_app_cmd = next((cmd for cmd in ["open", "xdg-open", "gnome-open", "kde-open"] if shutil.which(cmd)), None)
where_cmd         = next((cmd for cmd in ["where", "which"] if shutil.which(cmd)), None)

class Variables:
    is_from_launcher = is_from_launcher
    launcher_path    = launcher_path

    is_running = True
    is_paused = True

    is_roblox_focused = True
    is_selecting_region = None

    # macro settings #
    session_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    current_version = "2.0.4" if not is_from_launcher else "MATRIX.VERSION"
    current_branch  = "dev"   if not is_from_launcher else "MATRIX.BRANCH"

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
            logging.info(F"Opening: {url}")
            webbrowser.open(url)
        except Exception as e:
            logging.error(f"Failed to open link '{url}': {e}")

class StaticVariables:
    assets_folder                 = get_resource_path("assets")

    icon_filepath                 = os.path.join(assets_folder, "icons", "icon.ico")
    macos_icon_filepath           = os.path.join(assets_folder, "icons", "macos_icon.icns")

    ui_filepath                   = os.path.join(assets_folder, "ui", "ui.html")
    guide_ui_filepath             = os.path.join(assets_folder, "ui", "guide.html")
    rose_pine_lib_path            = os.path.join(assets_folder, "rose-pine")

    storage_folder                = get_base_path("storage")
    # temp_folder                 = os.path.join(storage_folder, "temp")
    
    config_filepath               = os.path.join(storage_folder, "config.ini")
    region_filepath               = os.path.join(storage_folder, "region.json")
    pathfinding_macros_filepath   = os.path.join(storage_folder, "pathfinding_macros.json")
    discord_config_filepath       = os.path.join(storage_folder, "discord_settings.json")
    
    logs_folder                   = os.path.join(storage_folder, "logs")
    log_filepath                  = os.path.join(logs_folder, Variables.session_id + ".log")
    crash_log_filepath            = os.path.join(logs_folder, Variables.session_id + "_crash.log")

    screenshots_folder            = os.path.join(storage_folder, "screenshots")
    prediction_screenshots_folder = os.path.join(screenshots_folder, "prediction", Variables.session_id)