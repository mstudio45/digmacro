import sys, subprocess, importlib
from utils.packages.distro_variables import *
from utils.packages.versions import check_package_version

__all__ = ["check_pip_packages"]
required_packages = {
    "all": [
        { "pip": "opencv-python",   "import": "cv2",            "version": "all" },
        { "pip": "numpy",           "import": "numpy",          "version": "all" },
        { "pip": "PyAutoGUI",       "import": "pyautogui",      "version": "all" },
        { "pip": "mss",             "import": "mss",            "version": "all" },
        { "pip": "screeninfo",      "import": "screeninfo",     "version": "all" },
        { "pip": "pynput",          "import": "pynput",         "version": "1.8.1" },
        { "pip": "requests",        "import": "requests",       "version": "all" },
        { "pip": "PySide6",         "import": "PySide6",        "version": "all" },
        { "pip": "psutil",          "import": "psutil",         "version": "all" },
        { "pip": "logging",         "import": "logging",        "version": "all" },
        { "pip": "pillow",          "import": "PIL",            "version": "all" }
    ],

    "Windows": [
        { "pip": "pywebview",        "import":  "webview",      "version": "all" },
        { "pip": "bettercam",        "import":  "bettercam",    "version": "all" },
        { "pip": "PyGetWindow",      "import":  "pygetwindow",  "version": "all" },
        { "pip": "pywin32",          "import":  "win32gui",     "version": "all" },
        { "pip": "PyAutoIt",         "import":  "autoit",       "version": "all" }
    ],

    "Linux": [
        { "pip": "pywebview[gtk]",   "import": "webview",       "version": "all" },
    ],

    "Darwin": [
        { "pip": "pywebview",        "import": "webview",       "version": "all" },
        { "pip": "PyObjC",           "import": "AppKit",        "version": "all" }
    ]
}
check_import_only = ["pywebview[gtk]"]

if current_os not in required_packages: 
    def check_pip_packages(): 
        print("[check_pip_packages] There are no packages to install for this OS.")
        return False

else:
    def check_pip_packages():
        compiled = "__compiled__" in globals()
        if compiled: 
            print("[check_pip_packages] Compiled mode, skipping...")
            return False

        freeze_list = subprocess.check_output([sys.executable, "-m", "pip", "freeze"])
        installed_packages = [r.decode().split("==") for r in freeze_list.split()]

        # get relevant packages #
        relevant_packages = required_packages.get("all", []) + required_packages.get(current_os, [])

        print(f"[check_pip_packages] Checking missing packages (packages['all'] + packages['{current_os}'])...")

        # get missing packages #
        missing_packages = []
        for package in relevant_packages:
            pip_name = package["pip"]
            import_name = package["import"]
            min_version = package["version"]

            # check pip freeze list #
            if pip_name not in check_import_only:
                installed_package = next((item for item in installed_packages if item[0] == pip_name), None)
                if installed_package is None:
                    print(f"[check_pip_packages] Package '{pip_name}' is not installed.")
                    missing_packages.append(package)
                    continue

                if min_version != "all" and not check_package_version(installed_package[1], min_version):
                    print(f"[check_pip_packages] Package '{pip_name}' is too old: {installed_package[1]} < {min_version}")
                    missing_packages.append(package)
                    continue
            
            # check import #
            try: importlib.import_module(import_name)
            except ImportError: 
                print(f"[check_pip_packages] Package '{pip_name}' didn't import properly.")
                missing_packages.append(package)

        # install packages #
        if len(missing_packages) == 0: 
            print("[check_pip_packages] All required packages are installed.\n")
            return False

        print(f"[check_pip_packages] Missing packages detected: {missing_packages}")
        for package in missing_packages: install_pip_package(package)
        
        print("[check_pip_packages] Done.\n")
        return True