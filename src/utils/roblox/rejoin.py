import time, webbrowser, platform
import subprocess, logging

from config import Config
from variables import Variables

from utils.input.keyboard import press_key
from utils.input.mouse import left_click

from utils.roblox.logstatus import RobloxStatusHandler
import utils.roblox.window as RobloxWindow

current_os = platform.system()

# rejoin stuff #
roblox_status_handler = RobloxStatusHandler()
roblox_status_handler.start()

def can_rejoin(total_idle_time):
    if not RobloxWindow.is_roblox_running(): 
        logging.info("Rejoining: Roblox is not running...")
        return True

    if roblox_status_handler.can_use_dynamic_rejoiner:
        # check log file status #
        if roblox_status_handler.disconnected == True:
            logging.info("Rejoining: Disconnected.")
            return True
        
        if roblox_status_handler.game_left == True:
            logging.info("Rejoining: Roblox is running, but not in-game.")
            return True

        if roblox_status_handler.roblox_closed == True:
            logging.info("Rejoining: Roblox is closed.")
            return True
    else:
        logging.critical("Auto Rejoin cannot use dynamic status handler (detecting Disconnect, Game leaving etc) through log files -> Roblox 'logs' folder was not found.")

    if Config.AUTO_REJOIN_INACTIVITY_TIMEOUT > 0.1 and total_idle_time >= (Config.AUTO_REJOIN_INACTIVITY_TIMEOUT * 60): return True

def create_rotocol(): 
    return "roblox://experiences/start?placeId=126244816328678&linkCode=" + str(Config.PRIVATE_SERVER_CODE)

def launch_protocol(protocol):
    global current_os
    
    RobloxWindow.kill_roblox()
    time.sleep(0.25)

    if current_os == "Windows":
        webbrowser.open(protocol)
        return

    subprocess.Popen(
        [Variables.unix_open_app_cmd, protocol],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def rejoin_dig():
    if not Config.AUTO_REJOIN: return
    if Variables.is_paused: logging.debug("Paused, skipping..."); return
    if not Variables.is_idle(): return

    logging.info("Rejoining...")
    Variables.is_rejoining = True
    protocol = create_rotocol()

    # leave the current game #
    if RobloxWindow.is_roblox_running():
        if roblox_status_handler.disconnected:
            logging.info(f"Disconnected with the reason: {roblox_status_handler.disconnected_error_code}")
        
        elif roblox_status_handler.game_left:
            logging.info("We are in the Roblox main menu, joining...")

        elif roblox_status_handler.playing:
            logging.info("We are still in the game, using keyboard inputs to leave - we don't want to break the save data in that server...")

            RobloxWindow.focus_roblox()
            time.sleep(0.5)

            left_click()
            time.sleep(0.1)

            press_key("esc", duration=0.1)
            press_key("l", duration=0.1)
            press_key("enter", duration=0.1)
        
            start = time.time()
            while roblox_status_handler.game_left == False: # loop until game_left is not False #
                if (time.time() - start) >= 2:
                    if roblox_status_handler.disconnected: 
                        break # successfully disconnected #
                
                if Variables.sleep(0.5): 
                    break # macro stopped #
            if not Variables.is_running: return

            logging.info("Successfully left the game, waiting for a moment before rejoining...")
            if Variables.sleep(2): return

    # rejoin the game #
    launch_protocol(protocol)
    if Variables.sleep(5): return

    # wait for the user to join #
    start_time = time.time()
    while Variables.is_running:
        if not Variables.is_roblox_focused: RobloxWindow.focus_roblox()
        if roblox_status_handler.playing: break # rejoined!

        if time.time() - start_time > 45: # if it still didnt find the shop btn for over 45 seconds, restart the process
            launch_protocol(protocol)
            start_time = time.time()
        
        if Variables.sleep(1.5): break

    if not Variables.is_running: return

    # rejoined successfully - wait 10 seconds for the game to fully load #
    logging.info("Rejoined, waiting 10 seconds for the game to load...")
    if Variables.sleep(10): return

    logging.info("Focusing Roblox...")
    RobloxWindow.focus_roblox()
    time.sleep(0.1)

    # reset variables since we rejoined #
    Variables.is_minigame_active = False
    Variables.is_walking = False
    Variables.is_selling = False
    Variables.last_minigame_interaction = None

    time.sleep(0.1)
    logging.info("Successfully rejoined.")
    Variables.is_rejoining = False