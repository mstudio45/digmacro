import time, webbrowser, shutil
import subprocess, logging

from config import Config
from variables import Variables, StaticVariables

import utils.roblox.window as RobloxWindow
from utils.images.screen_images import find_image, resize_image

__all__ = ["can_rejoin", "rejoin_dig"]

# images #
topbar_btn = resize_image(StaticVariables.topbar_btns_imgpath)
reconnect_btn = resize_image(StaticVariables.reconnect_btn_imgpath)

# rejoin stuff #
def create_rotocol(): return "roblox://experiences/start?placeId=126244816328678&linkCode=" + str(Config.PRIVATE_SERVER_CODE)
def can_rejoin(total_idle_time, sct):
    if not RobloxWindow.is_roblox_running(): return True
    if total_idle_time >= Config.AUTO_REJOIN_INACTIVITY_TIMEOUT * 60: return True
    if find_image(reconnect_btn, Config.AUTO_REJOIN_RECONNECT_CONFIDENCE, sct) is not None: return True
    
    return False

# rejoin handlers #
def launch_protocol(protocol):
    global current_os
    
    RobloxWindow.kill_roblox()
    time.sleep(0.1)
    if current_os == "Windows":
        webbrowser.open(protocol)
        return

    subprocess.Popen(
        [Variables.unix_macos_open_cmd, protocol],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def rejoin_dig(sct):
    if not Config.AUTO_REJOIN: return
    if not Variables.is_idle(): return

    logging.info("Rejoining...")
    Variables.is_rejoining = True
    protocol = create_rotocol()

    launch_protocol(protocol)
    if Variables.sleep(5): return

    found_times = 0
    start_time = time.time()

    while Variables.is_running:
        time.sleep(1.5)
        
        if not Variables.is_roblox_focused: RobloxWindow.focus_roblox()
        img = find_image(topbar_btn, Config.AUTO_REJOIN_CONFIDENCE, sct, log=True)

        if img is not None: found_times = found_times + 1
        if found_times >= 3: break # found it 3 times to be 100% sure

        if time.time() - start_time >= 30: # if it still didnt find the shop btn for over 30 seconds, restart the process
            launch_protocol(protocol)
            start_time = time.time()

    if Variables.is_running:
        logging.info("Rejoined!")
        if Variables.sleep(0.5): return
        RobloxWindow.focus_roblox()
        time.sleep(0.1)

    # reset variables since we rejoined #
    Variables.is_minigame_active = False
    Variables.is_walking = False
    Variables.is_selling = False
    Variables.last_minigame_interaction = None

    time.sleep(0.1)
    Variables.is_rejoining = False