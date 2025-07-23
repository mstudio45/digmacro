import traceback
import subprocess
import platform
import logging
import psutil

__all__ = ["is_roblox_focused", "focus_roblox", "kill_roblox", "is_roblox_running"]
current_os = platform.system()

if current_os == "Windows":
    logging.info("Using 'Windows' for Roblox window handler...")

    import win32gui
    import win32con
    import pygetwindow
    
    def is_roblox_focused():
        try:
            title = pygetwindow.getActiveWindowTitle()
            if not title: return False

            return "Roblox" == title
        except Exception as e: logging.error(f"Error checking focus on Roblox: {traceback.format_exc()}")
        
    def focus_roblox():
        try:
            roblox_window = pygetwindow.getWindowsWithTitle("Roblox")
            if not roblox_window: return
            roblox_window = roblox_window[0]

            roblox_window.activate()
            roblox_window.show()

            win32gui.ShowWindow(roblox_window._hWnd, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(roblox_window._hWnd)
        except Exception as e: logging.error(f"Error focusing Roblox: {traceback.format_exc()}")

    def kill_roblox(): subprocess.call("TASKKILL /F /IM RobloxPlayerBeta.exe")
    def is_roblox_running(): return "robloxplayerbeta.exe" in [p.name().lower() for p in psutil.process_iter()]

elif current_os == "Linux": # xdotool
    logging.info("Using 'Linux' for Roblox window handler...")

    def is_roblox_focused():
        try:
            root = subprocess.Popen(["xprop", "-root", "_NET_ACTIVE_WINDOW"], stdout=subprocess.PIPE)
            stdout, _ = root.communicate()
            active_window_id = stdout.strip().split()[-1]
            
            if active_window_id:
                title_proc = subprocess.Popen(["xprop", "-id", active_window_id, "WM_NAME"], stdout=subprocess.PIPE)
                stdout, _ = title_proc.communicate()
                title = stdout.strip().decode("utf-8", "ignore")

                return f'"sober"' in title.lower()
            return False
        except Exception as e: logging.error(f"Error checking focus on Roblox: {traceback.format_exc()}")
        
    def focus_roblox():
        try:
            result = subprocess.check_output(["xdotool", "search", "--class", "sober"])
            window_ids = result.decode().strip().split("\n")
            if not window_ids: return

            subprocess.call(["xdotool", "windowactivate", "--sync", window_ids[0]])
        except Exception as e: logging.error(f"Error focusing Roblox: {traceback.format_exc()}")
        
    def kill_roblox(): subprocess.call(["pkill", "-x", "sober"])
    def is_roblox_running(): return "sober" in [p.name().lower() for p in psutil.process_iter()]

elif current_os == "Darwin":
    logging.info("Using 'Darwin' for Roblox window handler...")

    from AppKit import NSWorkspace # type: ignore

    def is_roblox_focused():
        active_app = NSWorkspace.sharedWorkspace().activeApplication()
        if not active_app: return False
        if "NSApplicationName" not in active_app: return False

        return active_app["NSApplicationName"] == "Roblox"
    
    def focus_roblox(): subprocess.call(["osascript", "-e", "'tell application \"Roblox\" to activate'"])
    def kill_roblox(): subprocess.call(["pkill", "-9", "-f", '"RobloxPlayer"'])
    def is_roblox_running(): return "robloxplayer" in [p.name().lower() for p in psutil.process_iter()]
