import logging, platform
from config import Config

__all__ = ["alert", "confirm"]
current_os = platform.system()

if current_os == "Darwin":
    logging.info("Using 'Darwin' message box handler...")

    import subprocess

    def run_osascript(script):
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logging.error(f"AppleScript error: {e.stderr}")
            return None

    def alert(message, title="DIG Macro by mstudio45", log_level=logging.INFO, bypass=False):
        if not message:
            return

        logging.log(level=log_level, msg=message, stacklevel=2)
        if Config.MSGBOX_ENABLED or bypass:
            # Determine the type of alert
            if log_level >= logging.CRITICAL or log_level >= logging.ERROR:
                icon = "stop"
            elif log_level == logging.WARNING:
                icon = "caution"
            else:
                icon = "note"

            script = f'display dialog "{message}" with title "{title}" buttons ["OK"] with icon {icon}'
            run_osascript(script)

    def confirm(message, title="DIG Macro by mstudio45", buttons=("Yes", "No")):
        btn_list = ", ".join(f'"{btn}"' for btn in buttons)
        default_button = f'default button "{buttons[0]}"' if buttons else ""

        script = f'display dialog "{message}" with title "{title}" buttons {{{btn_list}}} {default_button}'
        response = run_osascript(script)

        if response and response.startswith("button returned:"):
            return response.split(":")[1].strip()

        return None
else:
    logging.info("Using 'General' message box handler...")

    import tkinter as tk
    from tkinter import ttk, messagebox
    from utils.images.screen import logical_screen_region

    def alert(message, title="DIG Macro by mstudio45", log_level=logging.INFO, bypass=False):
        if not message: return

        logging.log(level=log_level, msg=message, stacklevel=2)
        if Config.MSGBOX_ENABLED or bypass:
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes("-topmost", True)

            if log_level >= logging.CRITICAL or log_level >= logging.ERROR:
                messagebox.showerror(title=title + " - Message", message=message, parent=root)
            elif log_level == logging.WARNING:
                messagebox.showwarning(title=title + " - Message", message=message, parent=root)
            else:
                messagebox.showinfo(title=title + " - Message", message=message, parent=root)
            
            root.destroy()

    def confirm(message, title="DIG Macro by mstudio45", buttons=("Yes", "No")):
        # create dialog #
        dialog = tk.Tk()

        if current_os == "Linux": dialog.wait_visibility(dialog)
        else: dialog.overrideredirect(True)
        dialog.wm_attributes("-topmost", True)

        result = tk.StringVar()

        dialog.title(title)
        dialog.grab_set()
        dialog.resizable(False, False)

        # create layout #
        main_frame = ttk.Frame(dialog, padding="20 15 20 15")
        main_frame.pack(expand=True, fill="both")

        message_label = ttk.Label(main_frame, text=message, wraplength=300, justify="center")
        message_label.pack(pady=(0, 20))

        button_frame = ttk.Frame(main_frame)
        button_frame.pack()

        # buttons handler #
        def on_button_click(button_text):
            result.set(button_text)
            dialog.destroy()
        
        for i, button_text in enumerate(buttons):
            button = ttk.Button(
                button_frame,
                text=button_text,
                command=lambda text=button_text: on_button_click(text),
                padding="5 2"
            )
            button.pack(side="left", padx=5)
            if i == 0: button.focus_set()

        # center the dialog #
        dialog.update_idletasks()
        dialog_width = dialog.winfo_reqwidth()
        dialog_height = dialog.winfo_reqheight()

        x_pos = (logical_screen_region["width"] // 2) - (dialog_width // 2)
        y_pos = (logical_screen_region["height"] // 2) - (dialog_height // 2)
        dialog.geometry(f"+{x_pos}+{y_pos}")

        # wait for result #
        dialog.wait_window()
        return result.get()