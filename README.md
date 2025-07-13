# DIG Macro

<p align="center">
    <img src="https://github.com/user-attachments/assets/a15c5e87-ab1e-44e6-be01-0fd095e00982" alt="Showcase video"> <br />
    Auto minigame macro for <a href="https://www.roblox.com/games/126244816328678/DIG" target="_blank">DIG</a>. <br />
    <i>Current version: 2.0.0 | <a href="/CHANGELOGS.md">Changelogs</a> | <a href="https://discord.gg/hrryPU6cqh" target="_blank">Discord Server</a></i>
</p>

## What is This?

DIG Macro is a tool that automatically plays the minigame in the roblox game [DIG](https://www.roblox.com/games/126244816328678/DIG).

## How does this work?

DIG Macro uses [Python](https://www.python.org/) and computer vision to detect when to click inside the digging minigame. It uses pywebview which is a wrapper around a web browser to create a custom GUI.

---

## 📑 Table of Contents

- [Features](#-features)
- [TO-DO and Known Issues](/TO-DO.md)
- [Supported Operating Systems](#-supported-operating-systems)
- [Quick Start](#-quick-start)
  - [Download and Run](#-download-and-run)
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

| Operating System          | Support Status     | Supported Versions                                                            | Tested On                             | Notes                                                                    |
| ------------------------- | ------------------ | ----------------------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------ |
| **Windows** (Recommended) | ✅ Full Support    | Windows 10 and newer                                                          | Windows 10, Windows 11                | Roblox UWP (Microsoft Store) is not supported                            |
| **Linux**                 | ✅ Full Support    | Most modern distributions (Ubuntu/Debian, RHEL/Fedora, Arch, OpenSUSE)        | Linux Mint 22.1 (Cinnamon X11)        | Wayland is not supported, Requires [Sober](https://sober.vinegarhq.org/) |
| **macOS**                 | 🟡 Partial Support | Refer to [macOS Stability Issues](#-macos-stability-issues)                   | Apple M3 16 GB, Sequoia 15.5 (Retina) | Macro might struggle with performance                                    |

_If you have improvements or patches for additional (or currently supported) operating system(s), feel free to submit a pull request._

###  **macOS Stability Issues**
| OS Version                  | RAM                 | CPU                 | Support Status      | Notes                                                                                             |
| --------------------------- | ------------------- | ------------------- | ------------------- | ------------------------------------------------------------------------------------------------- |
| Monterey 12.6.7+            | 8GB or more         | Apple Silicon       | ✅ Full Support     | **M3 chip** works better with external monitors                                                   |
| Monterey 12.6.7+            | 8GB or more         | Intel i5 and newer  | 🟡 Partial Support  | **Only source version works**, Requires a lot of config changes to make it work properly          |

---

## 🚀 Quick Start

### 📥 Download and Run

> [!WARNING]
> Some antivirus software may flag the standalone (pre-built) version as a **false positive**. <br />
> This is a common issue with **binary files (`.exe`/`.app`/`.bin`)** generated using Python compilers such as **Nuitka** or **PyInstaller/auto-py-to-exe**. These tools bundle Python code into a single binary file, which can sometimes trigger antivirus alerts despite the code being completely safe. <br /> <br />
> **All of our code is open source and publicly available!**

#### Standalone (pre-built) version

1. **Download the latest version for your Operating System:**
   - [Click here to go to Releases](https://github.com/mstudio45/digmacro/releases)
2. **Run the macro:**
   - **Windows:** Double-click `digmacro_windows.exe`.
   - **Linux:** Double-click `digmacro_linux.bin` or run `./digmacro_linux.bin` in your terminal.
   - **macOS:** Refer to the [macOS section](#-MacOS-Setup) below for help.

#### Source version

1. **Download the latest version:**
   - [MAIN (stable) - Download](https://github.com/mstudio45/digmacro/archive/refs/heads/dev.zip) | [DEV - Download](https://github.com/mstudio45/digmacro/archive/refs/heads/dev.zip)
2. **Extract the ZIP File:**
   - **Windows/Linux:** Right-click the downloaded zip file and select `Extract Here` or `Extract All`.
   - **macOS:** Double-click the downloaded zip file.
3. **Open the Folder:**
   - Go into the extracted `digmacro-[main/dev]` folder.
4. **Run the macro:**
   - **Windows:** Double-click `launch.bat` or run `launch.bat` in your terminal.
   - **Linux/macOS:** Run `sh launch.sh` in your terminal.

---

###  **macOS Setup**

#### Video Tutorial
<a href="https://youtu.be/KHdoO1UF_n0" title="Video Tutorial" target="_blank">
  <img src="https://raw.githubusercontent.com/mstudio45/digmacro/refs/heads/storage/tutorial_video.png" alt="Video Tutorial" width="500">
</a>

#### Text Tutorial
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

**1. Accessibility Permissions**

> Required for controlling mouse clicks and keyboard input
> Needed for the automation features to work

**How to grant:** System Preferences → Security & Privacy → Privacy → Accessibility → Add the application (digmacro_macos)

**2. Screen Recording Permissions**

> Required for taking screenshots to analyze the game state
> Used for image recognition and prediction systems

**How to grant:** System Preferences → Security & Privacy → Privacy → Screen Recording → Add the application (digmacro_macos)

**3. Input Monitoring Permissions**

> Required for keyboard and mouse event handling

**How to grant:** System Preferences → Security & Privacy → Privacy → Input Monitoring → Add the application (digmacro_macos)

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

- **Computer Vision is at the wrong place.**
  - Go to the `storage` folder and delete `region.json` file. Then you will be prompted to re-select your minigame region again.

- **Macro is missing clicks or not working well:**
  - The macro’s speed can be affected by several factors:
    1) Your CPU performance and Roblox FPS also impact how well the macro runs
    2) **mss on Windows** slows down the macro because of VSync

  - If you're having issues, try the following:
    1) Lower your in-game graphics and enable "Low Graphics" inside DIG settings
    2) Close background applications (ideally only have the macro and Roblox running)
    3) Adjust the configuration (MIN_CLICK_INTERVAL, TARGET_FPS, USE_PREDICTION, PLAYER_BAR_DETECTION)
    4) Change your screen resolution (for example 1080p to 720p)

- **Running from source with macOS is not working well:**
  - This may be due to using Python from Homebrew, please uninstall Python from homebrew and install it from the official site for the best experience running from source.
  
- **Need help?**
  - Check the [Changelogs](CHANGELOGS.md) for updates or create a new issue in this repository.

---

## 👥 Credits

- [upio (notpoiu)](https://github.com/notpoiu): UI Design and helped with macOS support and testing
