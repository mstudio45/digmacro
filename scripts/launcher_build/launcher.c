#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <limits.h>
#include <unistd.h>
#include <time.h>

#ifdef _WIN32
    #include <windows.h>
    #include <direct.h>
#elif __APPLE__
    #include <mach-o/dyld.h>
    #include <libgen.h>
    #include <sys/stat.h>
#else
    #include <sys/stat.h>
#endif

#ifdef _WIN32
    #define PATH_SEPARATOR "\\"
    #define PYTHON_INSTALLER "python-3.12.8-amd64.exe"
    #define PYTHON_URL "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
    #define PYTHON_CMD "python"
#else
    #define PATH_SEPARATOR "/"
    #define PYTHON_CMD "python3"
#endif

#define PROJECT_NAME "digmacro_src"
#define PROJECT_REPO "https://github.com/mstudio45/digmacro.git"
#define PROJECT_URL_TEMPLATE "https://github.com/mstudio45/digmacro/archive/refs/heads/%s.zip"
#define PROJECT_ZIP_FILE "digmacro_src.zip"

#ifdef _WIN32
    #define MAIN_SCRIPT "launch.bat"
    #define MAIN_SCRIPT_PREFIX "call"
#else
    #define MAIN_SCRIPT "launch.sh"
    #define MAIN_SCRIPT_PREFIX "sh"
#endif

// ------------------- Utility ------------------- //

int file_exists(const char *filename) {
    struct stat buffer;
    return (stat(filename, &buffer) == 0);
}

int dir_exists(const char *path) {
    struct stat st;
    return (stat(path, &st) == 0 && S_ISDIR(st.st_mode));
}

void make_dir(const char *path) {
    if (!dir_exists(path)) {
#ifdef _WIN32
        if (_mkdir(path) != 0) {
#else
        if (mkdir(path, 0755) != 0) {
#endif
            perror("mkdir");
            exit(1);
        }
    }
}

int get_realpath(const char *path, char *resolved_path) {
#ifdef _WIN32
    if (_fullpath(resolved_path, path, 2048) == NULL) {
        return -1;
    }
#else
    if (realpath(path, resolved_path) == NULL) {
        return -1;
    }
#endif
    return 0;
}

int execute_command(const char *command) {
    printf("Executing: %s\n", command);
    int result = system(command);
    if (result != 0) {
        printf("Command failed with exit code: %d\n", result);
    }
    return result;
}

int get_executable_path(char *buffer, size_t size) {
#ifdef _WIN32
    DWORD len = GetModuleFileName(NULL, buffer, (DWORD)size);
    if (len == 0 || len == size) return 0;
#elif __APPLE__
    uint32_t bufsize = (uint32_t)size;
    if (_NSGetExecutablePath(buffer, &bufsize) != 0) return 0;
#else
    ssize_t len = readlink("/proc/self/exe", buffer, size - 1);
    if (len == -1) return 0;
    buffer[len] = '\0';
#endif
    return 1;
}

// ------------------- Notifications ------------------- //
void show_notification(const char *message, const char *title, const char *icon_type) {
    printf("[%s - %s] %s\n", title, icon_type, message);

#ifdef _WIN32
    UINT icon_flag = MB_ICONINFORMATION;

    if (icon_type) {
        if (strcmp(icon_type, "error") == 0) {
            icon_flag = MB_ICONERROR;
        } else if (strcmp(icon_type, "warning") == 0) {
            icon_flag = MB_ICONWARNING;
        } else if (strcmp(icon_type, "information") == 0 || strcmp(icon_type, "info") == 0) {
            icon_flag = MB_ICONINFORMATION;
        }
    }

    MessageBox(NULL, message, title, MB_OK | icon_flag);

#elif __APPLE__
    const char *apple_icon = "note";
    
    if (icon_type) {
        if (strcmp(icon_type, "error") == 0) {
            apple_icon = "stop";
        } else if (strcmp(icon_type, "warning") == 0) {
            apple_icon = "caution";
        } else if (strcmp(icon_type, "information") == 0 || strcmp(icon_type, "info") == 0) {
            apple_icon = "note";
        } else if (strcmp(icon_type, "note") == 0) {
            apple_icon = "note";
        }
    }
    
    char command[2048];
    snprintf(command, sizeof(command), "osascript -e 'display dialog \"%s\" with title \"%s\" buttons {\"OK\"} default button \"OK\" with icon %s'", message, title, apple_icon);
    
    int result = system(command);
    if (result != 0) {
        snprintf(command, sizeof(command), "osascript -e 'display dialog \"%s\" with title \"%s\" buttons {\"OK\"} default button \"OK\"'", message, title);
        system(command);
    }

#else
    if (system("which notify-send > /dev/null 2>&1") == 0) {
        char command[2048];
        snprintf(command, sizeof(command), "notify-send -i dialog-%s \"%s\" \"%s\"", icon_type, title, message);
        system(command);
    } else {
        printf("[%s] %s\n", title, message);
    }
#endif
}

void show_error(const char *message) {
    show_notification(message, "DIG Macro", "error");
}

void show_warning(const char *message) {
    show_notification(message, "DIG Macro", "warning");
}

void show_info(const char *message) {
    show_notification(message, "DIG Macro", "information");
}

#ifdef __APPLE__
void show_note(const char *message) {
    show_notification(message, "DIG Macro", "note");
}
#else
void show_note(const char *message) {
    show_notification(message, "DIG Macro", "information");
}
#endif

// ------------------- Path Check ------------------- //

#ifdef _WIN32
#include <Lmcons.h>

const char *get_username() {
    static char username[256] = {0};

    DWORD size = sizeof(username);
    if (GetUserNameA(username, &size)) {
        return username;
    }

    return "YourUsername";
}

int check_path_windows() {
    char current_dir[MAX_PATH];
    char exe_path[MAX_PATH];
    
    if (GetCurrentDirectory(MAX_PATH, current_dir) == 0) {
        show_error("Warning: Could not determine current directory.\n");
        return 1;
    }
    
    if (GetModuleFileName(NULL, exe_path, MAX_PATH) == 0) {
        show_error("Warning: Could not determine executable path.\n");
        return 1;
    }
    
    printf("Launcher location: %s\n", exe_path);
    printf("Current directory: %s\n", current_dir);
    
    if (strchr(current_dir, ' ') != NULL) {
        char warn_msg[512];
        snprintf(warn_msg, sizeof(warn_msg),
            "The current path contains spaces: %s\n"
            "This may cause issues.\nConsider moving the launcher to a path without spaces.",
            current_dir);
        show_warning(warn_msg);
    }
    
    char current_lower[MAX_PATH];
    strcpy(current_lower, current_dir);
    _strlwr(current_lower);
    
    const char *problematic_folders[] = {
        "\\downloads",
        "\\documents", 
        "\\desktop",
        "\\pictures",
        "\\music",
        "\\videos",
        "\\onedrive",
        "\\dropbox",
        "\\google drive",
        "\\icloud",
        "\\appdata\\local\\temp",
        "\\temp",
        "\\windows\\temp",
        ":\\temp",
        ":\\tmp"
    };
    
    int num_problematic = sizeof(problematic_folders) / sizeof(problematic_folders[0]);
    int found_problematic = 0;
    
    for (int i = 0; i < num_problematic; i++) {
        size_t len_path = strlen(current_lower);
        size_t len_folder = strlen(problematic_folders[i]);

        if (len_path >= len_folder) {
            if (strcmp(current_lower + len_path - len_folder, problematic_folders[i]) == 0) {
                if (!found_problematic) {
                    found_problematic = 1;
                }

                printf("! Ends with problematic folder: %s\n", problematic_folders[i]);
            }
        }
    }
    
    if (found_problematic) {
        const char *user = get_username();
        char problem_msg[2048];
        snprintf(problem_msg, sizeof(problem_msg),
            "The launcher is running from a potentially problematic location:\n%s\n"
            "\nMove the launcher to a dedicated folder like:\n"
            "- C:\\Users\\%s\\Desktop\\digmacro\n"
            "- C:\\Users\\%s\\Documents\\digmacro\n"
            "- C:\\digmacro\n",
            current_dir, user, user);
        
        show_error(problem_msg);
        exit(1);
    }
    
    printf("\n");
    return 1;
}
#elif defined(__linux__) || defined(__APPLE__)
#include <ctype.h>

const char *get_username() {
    static char username[256] = {0};
    const char *user = getenv("USER");
    if (user && user[0] != '\0') {
        strncpy(username, user, sizeof(username) - 1);
        username[sizeof(username) - 1] = '\0';
        return username;
    }

    user = getlogin();
    if (user && user[0] != '\0') {
        strncpy(username, user, sizeof(username) - 1);
        username[sizeof(username) - 1] = '\0';
        return username;
    }

    return "YourUsername";
}

void strtolower(char *s) {
    while (*s) {
        *s = tolower((unsigned char)*s);
        s++;
    }
}

int check_path_posix() {
    char current_dir[PATH_MAX];
    if (getcwd(current_dir, sizeof(current_dir)) == NULL) {
        printf("Warning: Could not determine current directory.\n");
        return 1;
    }
    
    printf("Current directory: %s\n", current_dir);
    
    char current_lower[PATH_MAX];
    strncpy(current_lower, current_dir, sizeof(current_lower));
    current_lower[sizeof(current_lower) - 1] = 0;
    strtolower(current_lower);

    const char *user = get_username();
    char usernamehome[PATH_MAX];
#ifdef __APPLE__
    snprintf(usernamehome, sizeof(usernamehome), "/Users/%s", user);
#else
    snprintf(usernamehome, sizeof(usernamehome), "/home/%s", user);
#endif
    strtolower(usernamehome);

    const char *problematic_folders[] = {
        "/downloads",
        "/documents",
        "/desktop",
        "/pictures",
        "/music",
        "/videos",
        "/dropbox",
        "/google drive",
        "/icloud",
        "/tmp",
        usernamehome
    };
    
    int num_problematic = sizeof(problematic_folders) / sizeof(problematic_folders[0]);
    int found_problematic = 0;
    
    for (int i = 0; i < num_problematic; i++) {
        size_t len_path = strlen(current_lower);
        size_t len_folder = strlen(problematic_folders[i]);

        if (len_path >= len_folder) {
            if (strcmp(current_lower + len_path - len_folder, problematic_folders[i]) == 0) {
                if (!found_problematic) {
                    found_problematic = 1;
                }

                printf("! Ends with problematic folder: %s\n", problematic_folders[i]);
            }
        }
    }
    
    if (found_problematic) {
        char problem_msg[2048];
        snprintf(problem_msg, sizeof(problem_msg),
            "The launcher is running from a potentially problematic location:\n%s\n"
            "\nMove the launcher to a dedicated folder like:\n"
            "- /home/%s/digmacro/\n"
            "- /opt/digmacro/\n"
            "- /usr/local/digmacro/\n",
            current_dir, user);
        
        show_error(problem_msg);
        exit(1);
    }

    return 1;
}
#endif

// ------------------- Python Check ------------------- //

int parse_python_version(const char *output, int *major, int *minor, int *patch) {
    return sscanf(output, "Python %d.%d.%d", major, minor, patch) == 3;
}

int check_python_version(char *out_cmd, size_t out_cmd_size) {
    printf("Checking Python installation...\n");

    const char *python_commands[] = {
        "python3 --version 2>&1",
        "python --version 2>&1",
        "py -3.12 --version 2>&1",
        "py --version 2>&1",
    };
    const char *python_execs[] = {
        "python3",
        "python",
        "py -3.12",
        "py",
    };

    int num_commands = sizeof(python_commands) / sizeof(python_commands[0]);
    int major, minor, patch;

    for (int i = 0; i < num_commands; i++) {
        FILE *fp = popen(python_commands[i], "r");
        if (fp != NULL) {
            char output[128];
            if (fgets(output, sizeof(output), fp) != NULL) {
                pclose(fp);
                printf("Found: %s", output);

                if (parse_python_version(output, &major, &minor, &patch)) {
                    if (major == 3 && minor == 12 && (patch == 7 || patch == 8)) {
                        printf("Python %d.%d.%d is acceptable.\n", major, minor, patch);
                        
                        strncpy(out_cmd, python_execs[i], out_cmd_size - 1);
                        out_cmd[out_cmd_size - 1] = '\0';

                        return 1;
                    }
                }
            } else {
                pclose(fp);
            }
        }
    }

    show_error("Python 3.12.8 not found on your system.\n");
    return 0;
}

// ------------------- Install Python ------------------- //

#ifdef _WIN32
int install_python_windows() {
    printf("Installing Python 3.12.8 on Windows...\n");

    char download_cmd[512];
    snprintf(download_cmd, sizeof(download_cmd), "powershell -Command \"Invoke-WebRequest -Uri '%s' -OutFile '%s'\"", PYTHON_URL, PYTHON_INSTALLER);

    if (execute_command(download_cmd) != 0) {
        show_error("Failed to download Python installer.\n");
        exit(1);
    }

    char install_cmd[256];
    snprintf(install_cmd, sizeof(install_cmd), "%s /quiet InstallAllUsers=1 PrependPath=1", PYTHON_INSTALLER);

    if (execute_command(install_cmd) != 0) {
        show_error("Failed to install Python.\n");
        exit(1);
    }

    remove(PYTHON_INSTALLER);
    printf("Python installation completed.\n");
    return 1;
}
#elif __APPLE__
int install_python_macos() {
    printf("Python 3.12.8 not found. Prompting user...\n");

    show_warning("Python 3.12.8 is required.\nYou will be directed to the official installer.");

    execute_command("open 'https://www.python.org/ftp/python/3.12.8/python-3.12.8-macos11.pkg'");
    sleep(2);
    
    show_note("Once you have installed Python 3.12.8, click OK to continue.");

    char python_cmd[64];
    if (!check_python_version(python_cmd, sizeof(python_cmd))) {
        show_error("Python 3.12.8 is still not installed.\nPlease install it before running DIG Macro again.");
        exit(1);
    }

    printf("Python installation verified.\n");
    return 1;
}
#else
int install_python_unix() {
    // TO-DO
    
    return 1;
}
#endif

// ------------------- Download & Extract ------------------- //

const char *get_branch_from_args(int argc, char *argv[]) {
    const char *prefix = "--branch=";
    size_t prefix_len = strlen(prefix);

    for (int i = 1; i < argc; i++) {
        if (strncmp(argv[i], prefix, prefix_len) == 0) {
            const char *branch = argv[i] + prefix_len;
            if (strcmp(branch, "main") == 0 || strcmp(branch, "dev") == 0) {
                return branch;
            } else {
                printf("Warning: Unknown branch '%s', defaulting to 'main'\n", branch);
                return "main";
            }
        }
    }
    return "main";
}

int download_and_extract(const char *branch) {
    printf("Downloading DIG Macro ZIP file...\n");

    char project_zip_url[256];
    snprintf(project_zip_url, sizeof(project_zip_url), PROJECT_URL_TEMPLATE, branch);
    printf("Using branch: %s\n", branch);

#ifdef _WIN32
    char download_cmd[512];
    snprintf(download_cmd, sizeof(download_cmd), "powershell -Command \"Invoke-WebRequest -Uri '%s' -OutFile '%s'\"", project_zip_url, PROJECT_ZIP_FILE);
#else
    char download_cmd[512];
    snprintf(download_cmd, sizeof(download_cmd), "curl -L -o %s %s || wget -O %s %s", PROJECT_ZIP_FILE, project_zip_url, PROJECT_ZIP_FILE, project_zip_url);
#endif

    if (execute_command(download_cmd) != 0) {
        show_error("Failed to download DIG Macro Source ZIP file.");
        exit(1);
    }

    if (!file_exists(PROJECT_ZIP_FILE)) {
        show_error("DIG Macro Source ZIP file was not downloaded.");
        exit(1);
    }

    printf("Extracting DIG Macro files...\n");

#ifdef _WIN32
    char extract_cmd[512];
    snprintf(extract_cmd, sizeof(extract_cmd), "powershell -Command \"Expand-Archive -Path '%s' -DestinationPath 'temp_extract' -Force\"", PROJECT_ZIP_FILE);
#else
    char extract_cmd[256];
    snprintf(extract_cmd, sizeof(extract_cmd), "unzip -o %s -d temp_extract", PROJECT_ZIP_FILE);
#endif

    if (execute_command(extract_cmd) != 0) {
        show_error("Failed to extract DIG Macro Source ZIP file.");
        remove(PROJECT_ZIP_FILE);
        exit(1);
    }

    char move_cmd[512];
#ifdef _WIN32
    snprintf(move_cmd, sizeof(move_cmd), "powershell -Command \"Get-ChildItem temp_extract | Move-Item -Destination '%s' -Force\"", PROJECT_NAME);
#else
    snprintf(move_cmd, sizeof(move_cmd),
        "find temp_extract -maxdepth 1 -type d ! -path temp_extract -exec mv {} %s \\; 2>/dev/null || "
        "mv temp_extract/*/ %s/ 2>/dev/null || "
        "mv temp_extract/* %s/ 2>/dev/null",
        PROJECT_NAME, PROJECT_NAME, PROJECT_NAME);
#endif

    execute_command(move_cmd);

    remove(PROJECT_ZIP_FILE);
#ifdef _WIN32
    execute_command("rmdir /s /q temp_extract 2>nul");
#else
    execute_command("rm -rf temp_extract");
#endif

    if (!file_exists(PROJECT_NAME)) {
        show_error("DIG Macro extraction failed.");
        exit(1);
    }

    printf("DIG Macro extracted successfully.\n");
    return 1;
}

int install_digmacro(int force_update, const char *branch) {
    printf("Setting up DIG Macro...\n");

    if (file_exists(PROJECT_NAME)) {
        if (force_update) {
            printf("Force update requested. Removing existing directory...\n");
#ifdef _WIN32
            char remove_cmd[256];
            snprintf(remove_cmd, sizeof(remove_cmd), "rmdir /s /q %s", PROJECT_NAME);
#else
            char remove_cmd[256];
            snprintf(remove_cmd, sizeof(remove_cmd), "rm -rf %s", PROJECT_NAME);
#endif
            execute_command(remove_cmd);
            if (!download_and_extract(branch)) {
                printf("Failed to download and extract DIG Macro.\n");
                exit(1);
            }
        } else {
            printf("DIG Macro directory already exists. Use --update-source to force re-download.\n");
        }
    } else {
        if (!download_and_extract(branch)) {
            show_error("Failed to download and extract DIG Macro.\n");
            exit(1);
        }
    }
    
    return 1;
}

// ------------------- Launch ------------------- //

int launch_digmacro(int argc, char *argv[], const char *python_cmd) {
#ifdef __APPLE__
    char env_folder[sizeof(PROJECT_NAME) + 4];
    snprintf(env_folder, sizeof(env_folder), "%s/env", PROJECT_NAME);

    char env_dev_folder[sizeof(PROJECT_NAME) + 8];
    snprintf(env_dev_folder, sizeof(env_dev_folder), "%s/dev", env_folder);

    char venv_folder[sizeof(PROJECT_NAME) + 15];
    snprintf(venv_folder, sizeof(venv_folder), "%s/Darwin", env_dev_folder);
    
    make_dir(env_folder);
    make_dir(env_dev_folder);

    if (!dir_exists(venv_folder)) {
        printf("Creating virtual environment for Darwin...\n");

        char cmd[4096];
        snprintf(cmd, sizeof(cmd), "%s -m venv \"%s\"", python_cmd, venv_folder);

        if (execute_command(cmd) != 0) {
            show_error("Failed to create virtual environment folder.\n");
            exit(1);
        }
    }

    char venv_python[PATH_MAX];
    char venv_python_tmp[PATH_MAX];
    snprintf(venv_python_tmp, sizeof(venv_python_tmp), "%s/bin/python3", venv_folder);
    if (get_realpath(venv_python_tmp, venv_python) != 0) {
        show_error("Failed to get real path for virtual environment.\n");
        exit(1);
    }

    char launch_cmd[8192];
    int pos = snprintf(launch_cmd, sizeof(launch_cmd), "\"%s\" %s/src/main.py", venv_python, PROJECT_NAME);
#elif __linux__
    char env_folder[sizeof(PROJECT_NAME) + 4];
    snprintf(env_folder, sizeof(env_folder), "%s/env", PROJECT_NAME);

    char env_dev_folder[sizeof(PROJECT_NAME) + 8];
    snprintf(env_dev_folder, sizeof(env_dev_folder), "%s/dev", env_folder);

    char venv_folder[sizeof(PROJECT_NAME) + 14];
    snprintf(venv_folder, sizeof(venv_folder), "%s/Linux", env_dev_folder);
    
    make_dir(env_folder);
    make_dir(env_dev_folder);

    if (!dir_exists(venv_folder)) {
        printf("Creating virtual environment for Linux...\n");

        char cmd[4096];
        snprintf(cmd, sizeof(cmd), "%s -m venv \"%s\"", python_cmd, venv_folder);

        if (execute_command(cmd) != 0) {
            show_error("Failed to create virtual environment folder.\n");
            exit(1);
        }
    }

    char venv_python[PATH_MAX];
    char venv_python_tmp[PATH_MAX];
    snprintf(venv_python_tmp, sizeof(venv_python_tmp), "%s/bin/python3", venv_folder);
    if (get_realpath(venv_python_tmp, venv_python) != 0) {
        show_error("Failed to get real path for virtual environment.\n");
        exit(1);
    }

    char launch_cmd[8192];
    int pos = snprintf(launch_cmd, sizeof(launch_cmd), "\"%s\" %s/src/main.py", venv_python, PROJECT_NAME);
#elif _WIN32
    char env_folder[sizeof(PROJECT_NAME) + 4];
    snprintf(env_folder, sizeof(env_folder), "%s\\env", PROJECT_NAME);

    char env_dev_folder[sizeof(PROJECT_NAME) + 8];
    snprintf(env_dev_folder, sizeof(env_dev_folder), "%s\\dev", env_folder);

    char venv_folder[sizeof(PROJECT_NAME) + 16];
    snprintf(venv_folder, sizeof(venv_folder), "%s\\Windows", env_dev_folder);
    
    make_dir(env_folder);
    make_dir(env_dev_folder);

    if (!dir_exists(venv_folder)) {
        printf("Creating virtual environment for Windows...\n");

        char cmd[4096];
        snprintf(cmd, sizeof(cmd), "%s -m venv \"%s\"", python_cmd, venv_folder);

        if (execute_command(cmd) != 0) {
            show_error("Failed to create virtual environment folder.\n");
            exit(1);
        }
    }

    char venv_python[4096];
    char venv_python_tmp[4096];
    snprintf(venv_python_tmp, sizeof(venv_python_tmp), "%s\\bin\\python.exe", venv_folder);
    if (get_realpath(venv_python_tmp, venv_python) != 0) {
        show_error("Failed to get real path for virtual environment. (bin)\n");
        exit(1);
    }

    if (!file_exists(venv_python)) {
        snprintf(venv_python_tmp, sizeof(venv_python_tmp), "%s\\Scripts\\python.exe", venv_folder);
        if (get_realpath(venv_python_tmp, venv_python) != 0) {
            show_error("Failed to get real path for virtual environment (Scripts).\n");
            exit(1);
        }
        
        if (!file_exists(venv_python)) {
            show_error("Python executable not found in virtual environment.\n");
            exit(1);
        }
    }

    char launch_cmd[8192];
    int pos = snprintf(launch_cmd, sizeof(launch_cmd), "\"%s\" %s\\src\\main.py", venv_python, PROJECT_NAME);
#endif

    for (int i = 1; i < argc; i++) {
        int remaining = sizeof(launch_cmd) - pos - 1;
        if (remaining <= 0) break;

        int written = snprintf(launch_cmd + pos, remaining, " \"%s\"", argv[i]);
        if (written < 0 || written >= remaining) break;
        pos += written;
    }

    return execute_command(launch_cmd);
}

// ------------------- Main ------------------- //

int main(int argc, char *argv[]) {
    char exe_path[PATH_MAX];
    if (!get_executable_path(exe_path, sizeof(exe_path))) {
        show_error("Could not determine launcher path.\n");
        exit(1);
    }

#ifdef __APPLE__
    char real_path[PATH_MAX];
    if (realpath(exe_path, real_path) == NULL) {
        show_error("Could not resolve real application path.\n");
        exit(1);
    }

    // Contents/MacOS -> Contents -> .app
    char *app_dir = dirname(real_path); // dirname(dirname(dirname(real_path)));
    if (chdir(app_dir) != 0) {
        show_error("Could not change working directory.\n");
        exit(1);
    }
    
    setenv("DYLD_LIBRARY_PATH", "", 1);
    setenv("DYLD_FRAMEWORK_PATH", "", 1);
    
    if (strstr(real_path, ".app/Contents/MacOS/") != NULL) {
        printf("Running from app bundle - setting up environment for Python operations\n");
        setenv("PATH", "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin", 1);
        strcpy(exe_path, app_dir);
    }
#endif

    printf("============ DIG Macro Launcher ============\n");
    
#ifdef _WIN32
    if (!check_path_windows()) {
        return 1;
    }
#elif defined(__linux__) || defined(__APPLE__)
    if (!check_path_posix()) {
        return 1;
    }
#else
    return 1; // unsupported platform
#endif

    printf("============ Checking Python ============\n");
    char python_cmd[64];
    if (!check_python_version(python_cmd, sizeof(python_cmd))) {
        printf("Python 3.12.8 not found. Installing...\n");

#ifdef _WIN32
        if (!install_python_windows()) {
            show_error("Failed to install Python 3.12.8, exiting.\n");
            return 1;
        }
#elif __APPLE__
        if (!install_python_macos()) {
            show_error("Failed to install Python 3.12.8, exiting.\n");
            return 1;
        }
#else
        if (!install_python_unix()) {
            show_error("Failed to install Python 3.12.8, exiting.\n");
            return 1;
        }
#endif

        memset(python_cmd, 0, sizeof(python_cmd));
        if (!check_python_version(python_cmd, sizeof(python_cmd))) {
            show_error("Python 3.12.8 installation verification failed. Please install manually.\n");
            return 1;
        }
    }
    
    printf("\n============ Checking DIG Macro Files ============\n");
    const char *branch = get_branch_from_args(argc, argv);
    int force_update = 0;

    char **new_argv = malloc(argc * sizeof(char *));
    if (!new_argv) {
        perror("malloc");
        exit(1);
    }

    int new_argc = 0;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--update-source") == 0) {
            force_update = 1;
        } else {
            new_argv[new_argc++] = argv[i];
        }
    }
    new_argv[new_argc] = NULL;

    if (!install_digmacro(force_update, branch)) {
        show_error("Failed to set up DIG Macro. Exiting.\n");
        return 1;
    }
    
    printf("\n============ Launching DIG Macro... ============\n");
    char **final_argv = malloc((new_argc + 2) * sizeof(char *));
    if (!final_argv) {
        perror("malloc");
        exit(1);
    }
    
    for (int i = 0; i < new_argc; i++) {
        final_argv[i] = new_argv[i];
    }
    
    char launcher_arg[2048];
    snprintf(launcher_arg, sizeof(launcher_arg), "--from-launcher=%s", exe_path);
    final_argv[new_argc] = launcher_arg;
    final_argv[new_argc + 1] = NULL;
    
    int result = launch_digmacro(new_argc + 1, final_argv, python_cmd);
    if (result != 0 && result != 9) {
        printf("\nDIG Macro exited with code: %d\n", result);
    }
    free(final_argv);

    return result;
}