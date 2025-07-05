> [!WARNING]
> **THIS IS A PRE-RELEASE VERSION OF THE NEXT UPDATE. IT IS WORK IN PROGRESS AND IT MAY NOT WORK CORRECTLY**

# DIG macro
<p align="center">
    <!-- <img src="https://raw.githubusercontent.com/mstudio45/digmacro/refs/heads/storage/showcase.gif" alt="Showcase video"> <br /> -->
    Auto minigame macro for <a href="https://www.roblox.com/games/126244816328678/DIG" target="_blank">DIG</a>. <br />
    <i>Current version: 2.0.0 | <a href="/CHANGELOGS.md">Changelogs</a></i>
</p>

## What is This?
DIG Macro is a tool that helps you play the [DIG Roblox minigame](https://www.roblox.com/games/126244816328678/DIG) automatically.

---

## 📑 Table of Contents
- [Features](#features)
- [Supported Operating Systems](#supported-operating-systems)
- [Quick Start](#quick-start)
  - [1. Download and Install](#1-download-and-install)
  - [2. Running the Macro](#2-running-the-macro)
- [How to Stop the Macro](#how-to-stop-the-macro)
- [Editing the Configuration](#editing-the-configuration)
  - [How to Open the Configuration](#how-to-open-the-configuration)
- [Pathfinding Macros (Movement Patterns)](#pathfinding-macros-movement-patterns)
  - [How to Add or Edit Movement Patterns](#how-to-add-or-edit-movement-patterns)
- [Troubleshooting](#troubleshooting)
- [Tips](#tips)

---

## Features
 * **Custom GUI**: A custom graphical interface with options and macro status.
 * **Configuration GUI**: A graphical interface that allows you to simply configure any macro setting and provides information about each one.
 * **Auto Sell**: Automatically sells your items after a given number of digs or after completing the pathfinding macro. (requires 'Sell Anywhere' gamepass)
 * **Auto Rejoin**: If you disconnect or something goes wrong, the macro will automatically rejoin DIG.
 * **Auto Start Minigame**: Starts the minigame automatically for you.
 * **Prediction System**: Predicts the player's bar position, resulting in faster digging.
 * **Pathfinding Macros**: A system that will move you around from where you started using various movement patterns (square, etc.).
 * **Boss Support**: You can use this macro to battle bosses.

---

## Supported Operating Systems
> [!NOTE]
> Both 32-bit and 64-bit systems are supported, but **64-bit is recommended for best performance**.  
> Administrator or sudo permissions may be required for some features on Linux/macOS.

* Windows (Recommended)
    - **Supported:** Windows 8, Windows 8.1, Windows 10, and Windows 11
    - **Tested on:** Windows 10, Windows 11
    - **Not officially supported:** Windows 7 (may work, but not tested)

* Linux
    - **Supported:** Most modern distributions, including Ubuntu, Debian, Linux Mint, Fedora, Arch, etc.
    - **Tested on:** Linux Mint 22.1 Cinnamon

* macOS
    - ⚠️ **Support is experimental and work-in-progress. The macro should run, but the detection/clicking handler will not work as of today.** ⚠️
    - *Support for macOS is being worked on the Apple M3 16 GB, Sequoia 15.5 (with Retina display)*

*If you have improvements or patches for additional (or currently supported) operating system(s), feel free to submit a pull request.*

---

## Quick Start

### 1. Download and Install
1. **Download the latest version:**
    - From releases: [Click here to go to Releases](https://github.com/mstudio45/digmacro/releases)
    - Source: [Click here to download](https://github.com/mstudio45/digmacro/archive/refs/heads/dev.zip) **Use this if you want to run the source or the `dev` version**
3. **Extract the ZIP File:**  
   Right-click the downloaded file and choose "Extract Here" or "Extract All".
4. **Open the Folder:**  
   Go into the extracted `digmacro-[windows/linux/macos/dev]` folder.

### 2. Running the Macro
- **Windows:** Double-click `launch.bat`
- **Linux/macOS:** Run `sh launch.sh` in your terminal

You will be asked:
- Whether to run from source (for developers) or standalone (for most users).
    - Press **1** to use the standalone version. (`digmacro.[exe/bin/app]` is required)
    - Press **2** to use the source version. (`src` folder is required)
- Whether to start the macro or edit the configuration.
    - Press **1** to start the macro.
    - Press **2** to edit the configuration of the macro.

---

## How to Stop the Macro
> [!NOTE]
> Keybind Shortcuts are not supported on macOS due to certain Python and OS restrictions.

- **Close the Macro Window:**  
  Just click the `close (X)` button or `Exit` button.
- **Keyboard Shortcuts:**
  Hold `Ctrl+E` or press `Ctrl+C` in the terminal window where the macro is running.
  
---

## Editing the Configuration
You can easily change how the macro works using a simple graphical interface.

### How to Open the Configuration
Follow the same steps as running the macro, but when asked **"What would you like to do?"**, simply enter **2** to edit the configuration instead of starting the macro.

---

## Pathfinding Macros (Movement Patterns)
The macro can move your character in different patterns (like a square, line, etc.). You can use the built-in patterns or create your own.

### How to Add or Edit Movement Patterns
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

## Troubleshooting
- **Macro is missing clicks or not working well:**  
  The macro's speed depends on your computer and Roblox's performance. Try lowering the speed in the configuration if you have issues.
- **Need help?**  
  Check the [Changelogs](CHANGELOGS.md) for updates or create a new issue in this repository.
