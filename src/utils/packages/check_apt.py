import sys
import traceback
import subprocess

from utils.packages.distro_variables import log_install, current_os, get_linux_app_install_cmd, get_linux_installed_packages, distro_key

__all__ = ["check_apt_packages"]
required_packages = {
    "Linux": {
        "all": {
            "gcc": "gcc",
        },

        "ubuntu_based": {
            "libgirepository1.0-dev": "libgirepository1.0-dev", 
            "libgirepository-2.0-dev": "libgirepository-2.0-dev",
            "libgtk-3-0t64": "libgtk-3-0",
            "libxcb-cursor-dev": "libxcb-cursor-dev"
        },

        "rhel_based": {
            "gobject-introspection-devel": "gobject-introspection-devel",
            "gtk3": "gtk3",
            "python3-gobject": "python3-gobject",
            "xcb-util-cursor": "xcb-util-cursor"
        },

        "arch_based": {
            "gobject-introspection": "gobject-introspection",
            "gtk3": "gtk3",
            "xcb-util-cursor": "xcb-util-cursor"
        },

        "opensuse_based": {
            "gobject-introspection-devel": "gobject-introspection-devel",
            "gtk3-devel": "gtk3-devel",
            "xcb-util-cursor-devel": "xcb-util-cursor-devel"
        }
    }
}

if current_os not in required_packages: 
    def check_apt_packages(): 
        log_install("[check_apt_packages] There are no packages to install for this OS.")
        return False
else:
    installed_packages = get_linux_installed_packages()
    if isinstance(installed_packages, str):
        log_install(installed_packages)
        sys.exit(1)

    # get relevant packages #
    os_required = required_packages[current_os] 
    relevant_packages = list(os_required.get("all", {}).items()) + list(os_required.get(distro_key, {}).items())

    def check_apt_packages():
        log_install(f"[check_apt_packages] Checking missing packages ({current_os}['all'] + {current_os}['{distro_key}'])...")

        # get missing packages #
        missing_packages = []
        for check_first, install_name in relevant_packages:
            if check_first in installed_packages: continue
            if install_name in installed_packages: continue

            missing_packages.append(install_name)

        if len(missing_packages) == 0: 
            log_install("[check_apt_packages] All required system packages are installed.\n")
            return False
        
        compiled = "__compiled__" in globals()
        if compiled:
            if current_os == "Linux":
                try: subprocess.run(["notify-send", "-t", "60", "DIG Macro", f"You are missing required packages. Install them manually: {missing_packages}"])
                except: pass

            log_install(f"You are missing required packages. Install them manually: {missing_packages}")
            sys.exit(1)
            return False
        
        # get install command #
        base_install_cmd = []
        if current_os == "Linux":
            base_install_cmd = get_linux_app_install_cmd()
            if isinstance(base_install_cmd, str):
                try: subprocess.run(["notify-send", "-t", "60", "DIG Macro", base_install_cmd])
                except: pass
                
                log_install(base_install_cmd)
                sys.exit(1)

        # install packages #
        for missing_package in missing_packages:
            try:
                install_cmd = base_install_cmd + [missing_package]
                log_install(f"[check_apt_packages] Installing system package: {missing_package} using {install_cmd}")
                subprocess.check_call(install_cmd)
            except Exception as e:
                log_install(f"[check_apt_packages] Failed to install '{missing_package}' requirement: \n{traceback.format_exc()}")
                sys.exit(1)
        
        log_install("[check_apt_packages] Done.\n")
        return True