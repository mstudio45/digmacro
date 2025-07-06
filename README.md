# DIG macro

<p align="center">
    <img src="https://github.com/user-attachments/assets/a15c5e87-ab1e-44e6-be01-0fd095e00982" alt="Showcase video"> <br />
    Auto minigame macro for <a href="https://www.roblox.com/games/126244816328678/DIG" target="_blank">DIG</a>. <br />
    <i>Current version: 2.0.0 | <a href="/CHANGELOGS.md">Changelogs</a> | <a href="https://discord.gg/hrryPU6cqh" target="_blank">Discord Server</a></i>
</p>

## What is This?

DIG Macro is a tool that automatically plays the minigame in the roblox game [DIG](https://www.roblox.com/games/126244816328678/DIG).

## How does this work?

DIG Macro uses [python](https://www.python.org/) and computer vision to detect when to click inside the digging minigame. It uses pywebview which is a wrapper around a web browser to create a custom GUI.

---

## 📑 Table of Contents

- [Features](#-features)
- [TO-DO and Known Issues](/TO-DO.md)
- [Supported Operating Systems](#-supported-operating-systems)
- [Quick Start](#-quick-start)
  - [Download and Run](#-1-download-and-run)
    - [Running on macOS](#-macos-setup)
    - [Permissions on macOS](#-permissions-on-macos)
- [How to Stop the Macro](#%EF%B8%8F-how-to-stop-the-macro)
- [Editing the Configuration](#%EF%B8%8F-editing-the-configuration)
  - [How to Open the Configuration](#-how-to-open-the-configuration)
- [Pathfinding Macros (Movement Patterns)](#%EF%B8%8F-pathfinding-macros-movement-patterns)
  - [How to Add or Edit Movement Patterns](#-how-to-add-or-edit-movement-patterns)
- [Troubleshooting](#-troubleshooting)
- [Credits](#-credits)

---

## ✨ Features

- **Custom GUI**: A custom graphical interface with options and macro status.
- **Configuration GUI**: A graphical interface that allows you to simply configure any macro setting and provides information about each one.
- **Auto Sell**: Automatically sells your items after a given number of digs or after completing the pathfinding macro. (requires 'Sell Anywhere' gamepass)
- **Auto Rejoin**: If you disconnect or something goes wrong, the macro will automatically rejoin DIG.
- **Auto Start Minigame**: Starts the minigame automatically for you.
- **Prediction System**: Predicts the player's bar position, resulting in faster digging.
- **Pathfinding Macros**: A system that will move you around from where you started using various movement patterns (square, etc.).
- **Boss Support**: You can use this macro to battle bosses.

---

## 💻 Supported Operating Systems

> [!NOTE]
> Both 32-bit and 64-bit systems are supported, but **64-bit is recommended for best performance**.  
> Administrator or sudo permissions may be required for some features on Linux/macOS.

| Operating System          | Support Status  | Supported Versions                                                         | Tested On                             | Notes                                |
| ------------------------- | --------------- | -------------------------------------------------------------------------- | ------------------------------------- | ------------------------------------ |
| **Windows** (Recommended) | ✅ Full Support | Windows 10 and newer                                                       | Windows 10, Windows 11                | Best performance and compatibility   |
| **Linux**                 | ✅ Full Support | Most modern distributions (Ubuntu, Debian, Linux Mint, Fedora, Arch, etc.) | Linux Mint 22.1 (Cinnamon, X11)       | Wayland not tested                   |
| **macOS**                 | 🧪 Experimental | macOS Sequoia 15.5+                                                        | Apple M3 16 GB, Sequoia 15.5 (Retina) | Work-in-progress, known issues exist |

### macOS Feature Status

| Feature                      | Status          | Notes                                                                              |
| ---------------------------- | --------------- | ---------------------------------------------------------------------------------- |
| Main GUI Support             | ✅ Working      | No issues observed while testing                                                   |
| Configuration GUI Support    | ✅ Working      | No issues observed while testing                                                   |
| Region Selection GUI Support | ✅ Working      | No issues observed while testing                                                   |
| Box Detection                | ✅ Working      | No issues observed while testing                                                   |
| In Minigame Detection        | ⚠️ Issues exist | Fails to persist detection of being inside a minigame after clicking once or twice |
| Click Handler                | ⚠️ Issues exist | Due to minigame detection and some other issues, can fail to click sometimes       |

_If you have improvements or patches for additional (or currently supported) operating system(s), feel free to submit a pull request._

---

## 🚀 Quick Start

### 📥 Download and Run

#### Standalone (pre-built) version

1. **Download the latest version for your Operating System:**
   - [Click here to go to Releases](https://github.com/mstudio45/digmacro/releases)
2. **Run the macro:**
   - **Windows:** Double-click `digmacro_windows.exe`.
   - **Linux:** Double-click `digmacro_linux.bin` or run `./digmacro_linux.bin` in your terminal.
   - **macOS:** Double-click `digmacro_macos` or run `./digmacro_macos` in your terminal.

#### Source version

1. **Download the latest version:**
   - [Click here to download](https://github.com/mstudio45/digmacro/archive/refs/heads/main.zip)
2. **Extract the ZIP File:**
   - Right-click the downloaded file and choose "Extract Here" or "Extract All".
3. **Open the Folder:**
   - Go into the extracted `digmacro-main` folder.
4. **Run the macro:**
   - **Windows:** Double-click `launch.bat` or run `launch.bat` in your terminal.
   - **Linux:** Run `sh launch.sh` in your terminal.
   - **macOS:** Refer to the [macOS section](#-MacOS-Setup) below for help.

---

###  **macOS Setup**

1. **Download & unzip** `digmacro_macos.zip`, then double-click `digmacro_macos.app` to launch.

2. If you see a warning that the app is from an unidentified developer, you need to allow it in your security settings:
   - Go to **System Preferences → Security & Privacy → General**.
   - Click **"Open Anyway"** next to the message about the app being blocked.

**If you still cannot open the app after pressing open anyway (like not launching)** You can use the following command in terminal after changing directories to whereever the digmacro_macos.app file is found:

```bash
cd /path/to/digmacro_macos.app # Change this to the actual path where digmacro_macos.app is located like ~/Downloads/
xattr -dr com.apple.quarantine digmacro_macos.app
open digmacro_macos.app
```

#### 🔐 Permissions on macOS

> [!WARNING]
> Since you are giving **Terminal** all of these permissions, it is recommended that you disable them all after ending the macro.

**1. Accessibility Permissions**

> Required for controlling mouse clicks and keyboard input
> Needed for the automation features to work

**How to grant:** System Preferences → Security & Privacy → Privacy → Accessibility → Add the application (Terminal)

**2. Screen Recording Permissions**

> Required for taking screenshots to analyze the game state
> Used for image recognition and prediction systems

**How to grant:** System Preferences → Security & Privacy → Privacy → Screen Recording → Add the application (Terminal)

**3. Input Monitoring Permissions**

> Required for keyboard and mouse event handling

**How to grant:** System Preferences → Security & Privacy → Privacy → Input Monitoring → Add the application (Terminal)

---

## ⏹️ How to Stop the Macro

> [!NOTE]
> Keybind Shortcuts are not supported on macOS due to certain Python and OS restrictions.

- **Close the Macro Window:** Just click the `close (X)` button or `Exit` button.
- **Keyboard Shortcuts:** Hold `Ctrl+E` or press `Ctrl+C` in the terminal window where the macro is running.

---

## ⚙️ Editing the Configuration

You can easily change how the macro works using a simple graphical interface.

### 🔧 How to Open the Configuration

Follow the same steps as running the macro, but when asked **"What would you like to do?"**, simply select **Edit the configuration** to edit the configuration instead of starting the macro.

---

## 🗺️ Pathfinding Macros (Movement Patterns)

The macro can move your character in different patterns (like a square, line, etc.). You can use the built-in patterns or create your own.

### ➕ How to Add or Edit Movement Patterns

1. **Open the File:**  
   Go to the `storage` folder and open `pathfinding_macros.json` with a text editor (like Notepad).

2. **Understanding the Format:**  
   Each pattern is a list of steps. Each step tells the macro which key(s) to press and for how long.

   - **Single Key:**  
     `"w"` means press W.
   - **Multiple Keys:**  
     `["w", "d"]` means press W and D together.
   - **Duration:**  
     The number (like `1.0`) is how many seconds to hold the key(s).

   **Example:**

   ```json
   "square": [
       ["w", 1.0],
       ["d", 1.0],
       ["s", 1.0],
       ["a", 1.0]
   ]
   ```

3. **Add Your Own Pattern:**  
   Add a new entry with your chosen name and steps.  
   For example, to add a "vertical_line" pattern:

   ```json
   {
     "vertical_line": [
       ["w", 2.0],
       ["s", 2.0]
     ],
     "square": [
       ["w", 1.0],
       ["d", 1.0],
       ["s", 1.0],
       ["a", 1.0]
     ]
   }
   ```

4. **Save the File:**  
   After editing, save the file. Your new pattern will appear in the configuration GUI.

---

## 🔧 Troubleshooting

- **Macro is missing clicks or not working well:**
  - The macro's speed depends on your computer and Roblox's performance. Try changing the configuration (MIN_CLICK_INTERVAL, TARGET_FPS) or your screen resolution if you have issues.
- **Running from source with macOS is not working well:**
  - This may be due to using Python from Homebrew, please uninstall python from homebrew and install it from the official site for the best experience running from source.
- **Need help?**
  - Check the [Changelogs](CHANGELOGS.md) for updates or create a new issue in this repository.

---

## 👥 Credits

- [upio (notpoiu)](https://github.com/notpoiu): UI Design and helped with macOS support and testing
