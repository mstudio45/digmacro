import time
import os
import platform
import logging
import traceback

if platform.system() == "Windows":
    from utils.detectors.roblox_memory.memory import PROCESS_QUERY_INFORMATION, PROCESS_VM_READ, EvasiveProcess, get_pid_by_name
    from utils.detectors.roblox_memory.rbxinstance import *

    import interface.msgbox as msgbox
    from variables import Variables

    class MemoryHandler:
        def __init__(self):
            self.setup_vars()
        
        # reset funcs #
        def setup_vars(self):
            self.loaded = False
            self.loading = False

            self.current_pid = None
            self.memory_module = None

            self.game = None
            # self.Workspace = None

            # localplayer instances #
            self.Players = None
            self.localPlayer = None
            self.character = None

            self.playerGui = None
            self.notificationsGui = None
            self.notificationFrame = None

            # replicated storage #
            self.ReplicatedStorage = None
            self.playerStats = None
            self.localPlayerStats = None
            self.localPlayerStatsStatsFolder = None
        
        def clear_everything(self):
            # stop memory module #
            try: self.memory_module.close()
            except Exception as e: logging.critical(f"Failed to close Memory Module... {traceback.format_exc()}")
            self.setup_vars()

        # memories #
        def reload_roblox_memory(self):
            if self.loading == True: return
            self.loading = True

            logging.info("Checking current roblox proccess for memory reloading...")
            
            pid = None
            while Variables.is_running:
                pid = get_pid_by_name("RobloxPlayerBeta.exe")
                if pid is not None and pid != 0: break
                time.sleep(0.1)

            if not Variables.is_running: self.loading = False; return
            if pid == self.current_pid: self.loading = False; return

            logging.info(f"Reloading Memory Module... (PID: {pid})")
            self.current_pid = pid
            self.memory_module = EvasiveProcess(pid, PROCESS_VM_READ | PROCESS_QUERY_INFORMATION)
            self.reload_datamodel()

        def reload_datamodel(self):
            logging.info("Waiting for DataModel...")

            game = None
            while Variables.is_running:
                game = DataModel(self.memory_module)
                if game.failed == False: break
                time.sleep(0.1)
            
            if not Variables.is_running: os.kill(os.getpid(), 9)
            if game.failed:
                msgbox.alert(f"Failed to load DataModel. Please restart the macro and try again.\n{str(game.error)}", log_level=logging.ERROR)
                os.kill(os.getpid(), 9)

            # game #
            self.game = game
            
            # localplayer instances #
            logging.info("Waiting for LocalPlayer...")
            self.Players = PlayersService(self.memory_module, self.game)
            self.localPlayer = self.Players.LocalPlayer
            self.character = self.localPlayer.Character

            logging.info("Waiting for Character...")
            if self.character is None:
                while self.character is None:
                    self.character = self.localPlayer.Character
                    time.sleep(0.1)
                    if not Variables.is_running: break
                if not Variables.is_running:
                    self.loading = False
                    self.loaded = False
                    return

            logging.info("Waiting for GUIs...")
            self.playerGui = self.localPlayer.WaitForChild("PlayerGui", self, 9e9)
            self.notificationsGui = self.playerGui.WaitForChild("Notifications", self, 9e9)
            self.notificationFrame = self.notificationsGui.WaitForChild("NotificationFrame", self, 9e9)

            # replicated storage #
            logging.info("Waiting for Player Stats...")
            self.ReplicatedStorage = self.game.GetService("ReplicatedStorage")
            self.playerStats = self.ReplicatedStorage.WaitForChild("PlayerStats", self, 9e9)
            self.localPlayerStats = self.playerStats.WaitForChild(self.localPlayer.Name, self, 9e9)
            self.localPlayerStatsStatsFolder = self.localPlayerStats.WaitForChild("Stats", self, 9e9)

            self.loading = False
            self.loaded = True
            logging.info(f"Memory Module and Data Model intialized, Player Username: {self.localPlayer.Name}")