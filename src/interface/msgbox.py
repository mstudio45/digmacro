import logging
import platform

__all__ = ["alert", "confirm"]
current_os = platform.system()

from variables import StaticVariables

if current_os == "Darwin":
    logging.info("Using 'Darwin' message box handler...")

    from Cocoa import NSApplication, NSAlert, NSImage, NSInformationalAlertStyle, NSWarningAlertStyle, NSCriticalAlertStyle # type: ignore
    import AppKit # type: ignore 

    def alert(message, title="DIG Macro by mstudio45", log_level=logging.INFO):
        if not message: return
        logging.log(level=log_level, msg=message, stacklevel=2)

        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)

        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(message)
        alert.addButtonWithTitle_("OK")

        if log_level >= logging.CRITICAL or log_level >= logging.ERROR:
            alert.setAlertStyle_(NSCriticalAlertStyle)
        elif log_level == logging.WARNING:
            alert.setAlertStyle_(NSWarningAlertStyle)
        else:
            try:
                icon = NSImage.alloc().initWithContentsOfFile_(StaticVariables.macos_icon_filepath)
                if icon: alert.setIcon_(icon)
            except:
                alert.setAlertStyle_(NSInformationalAlertStyle)
        
        app.activateIgnoringOtherApps_(True)
        alert.runModal()

    def confirm(message, title="DIG Macro by mstudio45", buttons=("Yes", "No")):
        if not message: return

        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)

        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(message)
        
        for button in buttons:
            alert.addButtonWithTitle_(button)
        
        try:
            icon = NSImage.alloc().initWithContentsOfFile_(StaticVariables.macos_icon_filepath)
            if icon: alert.setIcon_(icon)
        except:
            alert.setAlertStyle_(NSInformationalAlertStyle)
        
        app.activateIgnoringOtherApps_(True)
        response = alert.runModal()

        button_index = response - 1000
        if 0 <= button_index < len(buttons):
            return buttons[button_index]
        
        return None
else:
    logging.info("Using 'General' message box handler...")

    import tkinter as tk
    from tkinter import ttk, messagebox
    from utils.images.screen import logical_screen_region

    def alert(message, title="DIG Macro by mstudio45", log_level=logging.INFO):
        if not message: return
        logging.log(level=log_level, msg=message, stacklevel=2)

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
        if not message: return
        
        # create dialog #
        dialog = tk.Tk()
        dialog.iconbitmap(default=StaticVariables.icon_filepath)

        if current_os == "Linux": dialog.wait_visibility(dialog)
        dialog.wm_attributes("-topmost", True)

        result = tk.StringVar()

        # create dialog #
        dialog.title(title)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.configure(bg="white")

        # create style #
        style = ttk.Style(dialog)
        style.configure("White.TFrame", background="white")
        style.configure("White.TLabel", background="white")

        # create layout #
        main_frame = ttk.Frame(dialog, padding="20 15 20 15", style="White.TFrame")
        main_frame.pack(expand=True, fill="both")

        # create icon and label frame #
        content_frame = ttk.Frame(main_frame, style="White.TFrame")
        content_frame.pack(fill="x", pady=(0, 20))

        icon_label = tk.Label(content_frame, image="::tk::icons::question", bg="white")
        icon_label.pack(side="left", padx=(0, 5))

        message_label = ttk.Label(content_frame, text=message, wraplength=300, justify="left", anchor="w", style="White.TLabel")
        message_label.pack(side="left", fill="x", expand=True)

        button_frame = ttk.Frame(main_frame, style="White.TFrame")
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