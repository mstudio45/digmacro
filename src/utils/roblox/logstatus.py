import os, re, time, threading, platform, logging

from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

__all__ = ["RobloxStatusHandler"]
current_os = platform.system()

class RobloxLogFileHandler(FileSystemEventHandler):
    def __init__(self, log_finder):
        super().__init__()
        self.log_finder = log_finder

    def on_modified(self, event):
        if not event.is_directory and event.src_path == str(self.log_finder.current_log_file):
            self.log_finder.handle_log_file()

class RobloxStatusHandler:
    def __init__(self):
        self._stop_event = threading.Event()

        # status variables #
        self.current_log_file = None
        self.current_file_position = 0

        self.current_log_observer = None
        self.observer_handler = RobloxLogFileHandler(self)
        
        self.reset_state()

        # log information #
        self.file_name_patterns   = [ "*_Player_*.log" ]

        # joining keywords #
        self.keyword_game_joining = "[FLog::Output] ! Joining game"
        self.keyword_game_joined  = "[FLog::Network] serverId:"

        # disconnect #
        self.regex_error_code_reason = r"Sending disconnect with reason:\s*(\d+)"
        self.keyword_game_disconnected = "[FLog::Network] Sending disconnect with reason"
        self.keyword_game_leaving = "[DFLog::MegaReplicatorLogDisconnectCleanUpLog] Destroying MegaReplicator."

        # close #
        self.keyword_roblox_closing = "finished destroying luaApp"

        if current_os == "Windows":
            self.log_path = Path.home() / "AppData" / "Local" / "Roblox" / "logs"

        elif current_os == "Darwin": 
            self.log_path = Path.home() / "Library" / "Logs" / "Roblox"

        elif current_os == "Linux":
            self.log_path = Path.home() / ".var" / "app" / "org.vinegarhq.Sober" / "data" / "sober" / "appData" / "logs"
    
    # state handler #
    def reset_state(self):
        self.joining = False
        self.playing = False

        self.disconnected_error_code = "N/A"
        self.disconnected = False
        self.game_left = False

        self.roblox_closed = False

    # log finder #
    def find_latest_log_file(self):
        latest_file = None
        latest_time = 0
        
        if not self.log_path.exists():
            self.can_use_dynamic_rejoiner = False
            logging.debug(f"{str(self.log_path)} doesn't exist.")
            return None
        
        self.can_use_dynamic_rejoiner = True
        
        for pattern in self.file_name_patterns:
            for log_file in self.log_path.glob(pattern):
                if not log_file.is_file(): continue

                file_time = log_file.stat().st_mtime
                if file_time > latest_time:
                    latest_time = file_time
                    latest_file = log_file
        
        return latest_file
    
    # log file functions #
    def handle_log_file(self):
        logging.debug("Checking log file...")

        # read the current status #
        try:
            with open(self.current_log_file, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(self.current_file_position)
                for line in f: self.process_log_line(line.strip())
                self.current_file_position = f.tell()
        
        except (PermissionError, FileNotFoundError, OSError) as e:
            logging.debug(f"Error reading Roblox log file {self.current_log_file}: {e}")

        except Exception as e:
            logging.debug(f"Error reading Roblox log file {self.current_log_file}: {e}")

    def process_log_line(self, line):
        if self.keyword_game_joining in line:
            logging.info("Game joining detected")
            self.reset_state()
            self.joining = True
            return
        
        if self.keyword_game_joined in line:
            logging.info("Game joined")
            self.reset_state()
            self.playing = True
            return
        
        if self.keyword_game_disconnected in line:
            reason_match = re.search(self.regex_error_code_reason, line)
            reason_code = "N/A"

            if reason_match: reason_code = reason_match.group(1)

            logging.info(f"User Disconnected: {str(reason_code)}")
            self.reset_state()
            self.disconnected_error_code = str(reason_code)
            self.disconnected = True
            return
        
        if self.keyword_game_leaving in line:
            logging.info("User Left")
            self.reset_state()
            self.game_left = True
            return
        
        if self.keyword_roblox_closing in line:
            logging.info("Roblox Closed")
            self.reset_state()
            self.roblox_closed = True
            return
    
    # watchdog functions #
    def start_watchdog(self):
        logging.info("Starting watchdog...")
        self.stop_watchdog()

        if not self.log_path.exists():
            os.makedirs(str(self.log_path))

        self.current_log_observer = Observer()
        self.current_log_observer.schedule(self.observer_handler, path=self.log_path, recursive=False)
        self.current_log_observer.start()

    def stop_watchdog(self):
        if self.current_log_observer and self.current_log_observer.should_keep_running():
            logging.info("Stopping watchdog...")

            self.current_log_observer.stop()
            self.current_log_observer.join()
            self.current_log_observer = None

    # log finder #
    def start_log_finder(self):
        while not self._stop_event.is_set():
            latest_file = self.find_latest_log_file()
            
            if latest_file and str(latest_file) != str(self.current_log_file):
                logging.debug(f"Switching to new Roblox log file: {latest_file}")

                # reset states #
                self.current_log_file = latest_file
                self.current_file_position = 0
                self.reset_state()
                self.handle_log_file()

            time.sleep(2)

    # start/stop handler #
    def start(self):
        logging.info("Starting Roblox Player log monitoring...")
        
        # create threads #
        log_finder_thread = threading.Thread(target=self.start_log_finder, daemon=True)
        log_finder_thread.start()

        # create observer #
        self.start_watchdog()

    def stop(self):
        logging.info("Stopping Roblox log monitoring...")

        self._stop_event.set()
        self.stop_watchdog()

        logging.info("Roblox Log monitoring stopped")