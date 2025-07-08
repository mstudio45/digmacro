import os, sys, subprocess, platform, traceback
from utils.packages.distro_variables import install_pip_package, current_os

fixed_some_issue = False
def check_special_errors(import_error=False):
    global fixed_some_issue

    # check tkinter tcl issues #
    import tkinter as tk
    try:
        root = tk.Tk()
        root.withdraw()
        root.destroy()
    except (tk.TclError, ImportError) as e:
        if isinstance(e, ImportError):
            if import_error == True:
                print(f"[check_special_errors] Failed to properly install tkinter: {str(e)}")
                sys.exit(1)
            else:
                fixed_some_issue = True
                install_pip_package("tk")
                return check_special_errors(import_error=True) # restart again
        
        err_ = "Please setup the 'TCL_LIBRARY' and 'TK_LIBRARY' env variables manually and try again."
        if current_os != "Windows":
            print("[check_special_errors] " + err_)
            sys.exit(1)

        python_ver = platform.python_version()
        valid_python_path, valid_python_exe = "", ""

        paths_result = subprocess.run(["where", "python"], capture_output=True, text=True, check=True)
        paths = [line.strip() for line in paths_result.stdout.split("\n") if line.strip()]

        for path in paths:
            if path == sys.executable: continue

            version_result = subprocess.run([path, "--version"], capture_output=True, text=True)
            version_output = version_result.stdout.strip() or version_result.stderr.strip()

            if version_output.endswith(python_ver):
                valid_python_exe, valid_python_path = path, os.path.dirname(path)
                break
        
        if valid_python_path == "" or valid_python_exe == "":
            print(f"[check_special_errors] Failed to find the valid python path. {err_}")
            sys.exit(1)

        # get tcl version from exe #
        tcl_version_result = subprocess.run([valid_python_exe, "-c", "import tkinter; print(tkinter.TclVersion)"], capture_output=True, text=True)
        tcl_version_output = tcl_version_result.stdout.strip() or tcl_version_result.stderr.strip()

        tcl_path = os.path.join(valid_python_path, "tcl", "tcl" + str(tcl_version_output))
        tk_path = os.path.join(valid_python_path, "tcl", "tk" + str(tcl_version_output))

        if os.path.isdir(tcl_path) == False or os.path.isdir(tk_path) == False:
            print(f"[check_special_errors] Failed to find the valid tcl/tk path. {err_}")
            sys.exit(1)

        os.environ["TCL_LIBRARY"] = tcl_path
        os.environ["TK_LIBRARY"]  = tk_path

        fixed_some_issue = True
    except Exception as e:
        print(f"[check_special_errors] Failed to properly fix tkinter TCL and TK issue: {traceback.format_exc()}")

    print("[check_special_errors] Done.\n")
    return fixed_some_issue
