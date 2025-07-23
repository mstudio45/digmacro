import sys
import traceback
import subprocess
import shutil

from utils.packages.distro_variables import log_install, current_os, get_linux_app_install_cmd, distro_key

__all__ = ["check_shutil_applications"]
required_applications = {
    "Linux": {
        "all": [
            "xdotool",
            "pkg-config"
        ]
    }
}

if current_os not in required_applications: 
    def check_shutil_applications():
        log_install("[check_shutil_applications] There are no applications to install for this OS.")
        return False
else:
    # get relevant packages #
    os_required = required_applications[current_os] 
    relevant_packages = os_required.get("all", []) + os_required.get(distro_key, [])

    def check_shutil_applications():
        log_install(f"[check_shutil_applications] Checking missing applications ({current_os}['all'] + {current_os}['{distro_key}'])...")

        # get missing applications #
        missing_applications = []
        for cmd in relevant_packages:
            if shutil.which(cmd) is not None: continue
            missing_applications.append(cmd)

        if len(missing_applications) == 0: 
            log_install("[check_shutil_applications] All required applications are installed.\n")
            return False

        # get install command #
        base_install_cmd = []
        if current_os == "Linux":
            base_install_cmd = get_linux_app_install_cmd()
            if isinstance(base_install_cmd, str):
                log_install(base_install_cmd)
                sys.exit(1)

        # install applications #
        for missing_application in missing_applications:
            try:
                install_cmd = base_install_cmd + [missing_application]
                log_install(f"[check_shutil_applications] Installing application: {missing_application} using {install_cmd}")
                subprocess.check_call(install_cmd)
            except Exception as e:
                log_install(f"[check_shutil_applications] Failed to install '{missing_application}' requirement: \n{traceback.format_exc()}")
                sys.exit(1)
        
        log_install("[check_shutil_applications] Done.\n")
        return True