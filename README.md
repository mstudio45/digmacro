> [!WARNING]
> **THIS IS A PRE-RELEASE VERSION OF THE NEXT UPDATE. IT IS WORK IN PROGRESS AND IT MAY NOT WORK CORRECTLY**

# DIG macro
<p align="center">
    <img src="https://raw.githubusercontent.com/mstudio45/digmacro/refs/heads/storage/digmacro-showcase.gif" alt="Showcase video"> <br />
    Auto minigame macro for <a href="https://www.roblox.com/games/126244816328678/DIG" target="_blank">DIG</a>.  <br />
    <i>Current version: 2.0.0 | <a href="/CHANGELOGS.md">Changelogs</a></i>
</p>

## Table of Contents
* [Requirements](#requirements)
* [Features](#features)
* [Installation](#installation)
    * [How to Run](#how-to-run)
    * [How to Stop](#how-to-stop)
* [Configuration](#configuration)
    * [Pathfinding Macros Configuration](#pathfinding-macros)

## Features
 * **Configuration GUI**: GUI to easily configure each macro setting with information about each setting.
 * **Prediction system**: Predicts the player bar position to make digging faster.
 * **Pathfinding**: Macro will move you around the starting position with different pathfinding macros (square, etc.).
 * **Boss support**: This macro allows you to fight bosses with it.
 * **Auto Sell**: Automatically sells your items after certain amount of digs or after finishing the pathfinding macro. (requires 'Sell Anywhere' gamepass)
 * **Auto Rejoin**: Automatically rejoins DIG if you disconnect or if something went wrong.

## Requirements
 * [Python](https://www.python.org/) **[Recommended version: 3.13]**

## Installation
> [!WARNING]
> The speed of the macro can depend on your computer's performance and on current Roblox FPS. **This macro will missclick and could end your streak!**

1. **Download:** https://github.com/mstudio45/digmacro/archive/refs/heads/dev.zip
2. **Extract the downloaded zip file (digmacro-dev.zip).**
3. **Open the folder (digmacro-dev).**

### How to Run
> [!NOTE]
> If you are using the macro for the first time (or you deleted the `storage/pos.json` file) you need to **Change the in-game setting** `Minigame Dimming` to **`1`**. Afterwards you can set it to what value you want.

1. **Run the Script:**
    Simply run the macro by opening `start.bat` or `digmacro.exe`.

### How to Stop
  * Simply **close the macro window**.
  * Alternatively, you can hold `Ctrl+E` or press `Ctrl+C` in the terminal where the script is running.

## Configuration
  * Simply run `edit.bat` (or `digmacro.exe --edit-config`) to open the configuration GUI.

## Pathfinding Macros
The macro movement patterns are defined in a JSON file that specifies key presses and durations for each shape or pattern.

### Macro Format
Each macro consists of a list of keypress instructions. Each instruction is an array containing:

* **Key(s)**: Either a single key (e.g., `"w"`, `"a"`, `"s"`, `"d"`) or a combination of keys (e.g., `["w", "d"]` means pressing **W** and **D** together).
* **Duration**: A float representing how long (in seconds) to hold the key(s).

Example:

```json
"square": [
    ["w", 1.0],
    ["d", 1.0],
    ["s", 1.0],
    ["a", 1.0]
]
```

### How to Add New Macros

1. Open the macro configuration file (`storage/pathfinding_macros.json`) in a text editor.
2. Add a new key-value pair to the JSON object with your desired macro name and pattern.
   For example, to add a "vertical_line" shape:

   ```
   {
        "your_macro": [ ["w", 1.0], [["s", "d"], 0.5], ... ],
        "square: [ ... ],
        ...
   }
   ```
3. Save the file.
4. The new macro will now be available inside the configuration GUI.