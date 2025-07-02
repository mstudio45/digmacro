import os, psutil, time, subprocess
import win32gui

from config import Config
from utils.general.input import left_click
from variables import Variables, StaticVariables
import logging

from utils.screen_images import find_image, resize_image

__all__ = ["is_roblox_focused", "rejoin"]
gamepass_btn = resize_image(StaticVariables.gamepass_shop_btn_imgpath)
reconnect_btn = resize_image(StaticVariables.reconnect_btn_imgpath)

def is_roblox_focused():
    try:
        wnd = win32gui.GetForegroundWindow()
        if not wnd: return False
    
        title = win32gui.GetWindowText(wnd)
        return "roblox" == title.lower()
    except Exception as e:
        logging.error(f"Error checking focus: {e}")
        return False

def is_roblox_running():
    return "robloxplayerbeta.exe" in [p.name().lower() for p in psutil.process_iter()]

def kill_roblox():
    subprocess.call("TASKKILL /F /IM RobloxPlayerBeta.exe", shell=True)

def create_rotocol():
    return "roblox://placeID=126244816328678&linkCode=" + str(Config.PRIVATE_SERVER_CODE)

def can_rejoin(total_idle_time):
    if not is_roblox_running():
        return True

    if total_idle_time >= Config.AUTO_REJOIN_INACTIVITY_TIMEOUT * 60:
        return True
    
    if find_image(reconnect_btn, confidence=Config.AUTO_REJOIN_RECONNECT_CONFIDENCE) is not None:
        return True
    
    return False

def rejoin_dig():
    if not Config.AUTO_REJOIN: return
    if not Variables.is_idle(): return

    logging.info("Rejoining...")
    Variables.is_rejoining = True
    protocol = create_rotocol()

    def rejoin():
        kill_roblox()
        time.sleep(0.1)
        os.startfile(protocol)

    rejoin()

    found_times = 0
    start_time = time.time()

    while Variables.running:
        time.sleep(1.5)
        img = find_image(gamepass_btn, confidence=Config.AUTO_REJOIN_CONFIDENCE)

        if img is not None: found_times = found_times + 1
        if found_times >= 3: break # found it 3 times to be 100% sure

        if time.time() - start_time >= 30: # if it still didnt find the shop btn for over 30 seconds, restart the process
            rejoin()
            start_time = time.time()

    if Variables.running:
        logging.info("Rejoined!")
        time.sleep(0.5) # wait a bit longer for the game to fully load
        left_click() # focus roblox #
        time.sleep(0.25)

    Variables.is_rejoining = False
