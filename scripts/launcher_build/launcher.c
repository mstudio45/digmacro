#define _POSIX_C_SOURCE 200809L
#define _GNU_SOURCE

#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include <limits.h>
#include <stdlib.h>

#ifdef _WIN32
    #include <windows.h>
    #include <direct.h>
    #include <Lmcons.h>
#elif __APPLE__
    #include <ctype.h>
    #include <mach-o/dyld.h>
    #include <libgen.h>
    #include <sys/stat.h>
#else
    #include <ctype.h>
    #include <pwd.h>
    #include <sys/stat.h>
    #include <sys/types.h>
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

#define STR_PATH_MAX 4096
static char g_cwd[STR_PATH_MAX];
static char g_exe_path[STR_PATH_MAX];

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

#ifdef _WIN32
int get_realpath(const char *path, char *resolved_path) {
    if (_fullpath(resolved_path, path, 2048) == NULL) {
        return -1;
    }
    return 0;
}
#else
int get_realpath(const char *path, char *resolved_path) {
    if (realpath(path, resolved_path) == NULL) {
        return -1;
    }   
    return 0;
}
#endif

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
const char *get_username() {
    static char username[256] = {0};

    DWORD size = sizeof(username);
    if (GetUserNameA(username, &size)) {
        return username;
    }

    return "YourUsername";
}

int check_path_windows() {
    if (strchr(g_cwd, ' ') != NULL) {
        char warn_msg[512];
        snprintf(warn_msg, sizeof(warn_msg),
            "The current path contains spaces: %s\n"
            "This may cause issues.\nConsider moving the launcher to a path without spaces.",
            g_cwd);
        show_warning(warn_msg);
    }
    
    char current_lower[MAX_PATH];
    strcpy(current_lower, g_cwd);
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
            g_cwd, user, user);
        
        show_error(problem_msg);
        exit(1);
        return 0;
    }
    
    printf("\n");
    return 1;
}
#elif defined(__linux__) || defined(__APPLE__)
const char *get_username() {
    static char username[256] = {0};
    
    const char *user = getenv("USER");
    if (user && user[0] != '\0') {
        strncpy(username, user, sizeof(username) - 1);
        username[sizeof(username) - 1] = '\0';
        return username;
    }

#ifdef __linux__
    user = getenv("LOGNAME");
    if (user && user[0] != '\0') {
        strncpy(username, user, sizeof(username) - 1);
        username[sizeof(username) - 1] = '\0';
        return username;
    }

    struct passwd *pw = getpwuid(getuid());
    if (pw && pw->pw_name && pw->pw_name[0] != '\0') {
        strncpy(username, pw->pw_name, sizeof(username) - 1);
        username[sizeof(username) - 1] = '\0';
        return username;
    }
#endif

    user = getlogin();
    if (user && user[0] != '\0') {
        strncpy(username, user, sizeof(username) - 1);
        username[sizeof(username) - 1] = '\0';
        return username;
    }

    return "YourUsername";
}

void strtolower(char *s) {
    if (!s) return;
    while (*s) {
        *s = tolower((unsigned char)*s);
        s++;
    }
}

int check_path_posix() {
    char current_lower[STR_PATH_MAX];
    strncpy(current_lower, g_cwd, sizeof(current_lower) - 1);
    current_lower[sizeof(current_lower) - 1] = '\0';
    strtolower(current_lower);

    const char *user = get_username();
    if (!user) {
        show_error("Failed to get the username.");
        exit(1);
        return 1;
    }

    char usernamehome[STR_PATH_MAX];
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
            g_cwd, user);
        
        show_error(problem_msg);
        exit(1);
        return 0;
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

    const char *python_execs[] = {
        "python3",
        "python3.12",
        "python",
        "py -3.12",
        "py",
    };
    int num_commands = sizeof(python_execs) / sizeof(python_execs[0]);

    for (int i = 0; i < num_commands; i++) {
        char full_path[256] = "";

#ifdef _WIN32
        char path_cmd[256];
        snprintf(path_cmd, sizeof(path_cmd), "where %s", python_execs[i]);
        
        FILE *fp_path = popen(path_cmd, "r");
        if (fp_path != NULL) {
            char path_output[256];
            while (fgets(path_output, sizeof(path_output), fp_path) != NULL) {
                path_output[strcspn(path_output, "\r\n")] = '\0';
                if (strstr(path_output, "msys64") != NULL || strstr(path_output, "usr\\bin") != NULL) {
                    printf("Skipping MSYS2/Git Bash Python: %s\n", path_output);
                    continue;
                }
                
                strncpy(full_path, path_output, sizeof(full_path) - 1);
                full_path[sizeof(full_path) - 1] = '\0';
                break;
            }
            pclose(fp_path);
        }
#else
        strncpy(full_path, python_execs[i], sizeof(full_path) - 1);
        full_path[sizeof(full_path) - 1] = '\0';
#endif

        if (strlen(full_path) > 0) {
            char version_cmd[512];
#ifdef _WIN32
            snprintf(version_cmd, sizeof(version_cmd), "\"%s\" --version 2>&1", full_path);
#else
            snprintf(version_cmd, sizeof(version_cmd), "%s --version 2>&1", full_path);
#endif
            FILE *fp_version = popen(version_cmd, "r");
            if (fp_version != NULL) {
                char version_output[128];
                if (fgets(version_output, sizeof(version_output), fp_version) != NULL) {
                    pclose(fp_version);
                    printf("Found Python: %s", version_output);

                    int major, minor, patch;
                    if (parse_python_version(version_output, &major, &minor, &patch)) {
                        if (major == 3 && minor == 12 && (patch == 7 || patch == 8)) {
                            printf("Python %d.%d.%d is acceptable.\n", major, minor, patch);
                            
                            strncpy(out_cmd, full_path, out_cmd_size - 1);
                            out_cmd[out_cmd_size - 1] = '\0';
                            return 1;
                        }
                    }
                } else {
                    pclose(fp_version);
                }
            }
        }
    }

#ifdef _WIN32   
    show_error("Python 3.12.7 or 3.12.8 not found on your system or is from an unsupported environment (MSYS2/Git Bash).\n");
#else
    show_error("Python 3.12.7 or 3.12.8 not found on your system.\n");
#endif
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
        return 0;
    }

    char install_cmd[256];
    snprintf(install_cmd, sizeof(install_cmd), "%s /quiet InstallAllUsers=1 PrependPath=1", PYTHON_INSTALLER);

    if (execute_command(install_cmd) != 0) {
        show_error("Failed to install Python.\n");
        exit(1);
        return 0;
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

    char python_cmd[STR_PATH_MAX];
    if (!check_python_version(python_cmd, sizeof(python_cmd))) {
        show_error("Python 3.12.8 is still not installed.\nPlease install it before running DIG Macro again.");
        exit(1);
        return 0;
    }

    printf("Python installation verified.\n");
    return 1;
}
#else
int install_python_unix() {
    printf("Python 3.12.8 not found.\n");
    show_warning("Python 3.12.8 is required.\nPlease install it before running DIG Macro again.");
    exit(1);
    return 0;
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

    char project_zip_url[1024];
    snprintf(project_zip_url, sizeof(project_zip_url), PROJECT_URL_TEMPLATE, branch);
    printf("Using branch: %s\n", branch);

    char project_zip_path[STR_PATH_MAX];
    char temp_extract_path[STR_PATH_MAX];
    char project_name_path[STR_PATH_MAX];
    char env_path[STR_PATH_MAX];
    char env_backup_path[STR_PATH_MAX];

    char download_cmd[STR_PATH_MAX + 256];
    char extract_cmd[STR_PATH_MAX * 2 + 128];
    char move_cmd[STR_PATH_MAX * 3 + 256];
    char rm_cmd[STR_PATH_MAX + 64];    
    char backup_cmd[STR_PATH_MAX * 3 + 256];
    char restore_cmd[STR_PATH_MAX * 3 + 256];

    snprintf(project_zip_path, sizeof(project_zip_path), "%s%s%s", g_cwd, PATH_SEPARATOR, PROJECT_ZIP_FILE);
    snprintf(project_name_path, sizeof(project_name_path), "%s%s%s", g_cwd, PATH_SEPARATOR, PROJECT_NAME);
    snprintf(env_path, sizeof(env_path), "%s%senv", project_name_path, PATH_SEPARATOR);
    snprintf(env_backup_path, sizeof(env_backup_path), "%s%senv_backup", g_cwd, PATH_SEPARATOR);

#ifdef _WIN32
    snprintf(download_cmd, sizeof(download_cmd), "powershell -Command \"Invoke-WebRequest -Uri '%s' -OutFile '%s'\"", project_zip_url, project_zip_path);
#else
    snprintf(download_cmd, sizeof(download_cmd), "curl -L -o \"%s\" \"%s\" || wget -O \"%s\" \"%s\"", project_zip_path, project_zip_url, project_zip_path, project_zip_url);
#endif

    if (execute_command(download_cmd) != 0) {
        show_error("Failed to download DIG Macro Source ZIP file.");
        exit(1);
        return 0;
    }

    if (!file_exists(project_zip_path)) {
        show_error("DIG Macro Source ZIP file was not downloaded.");
        exit(1);
        return 0;
    }

    if (dir_exists(env_path) && !dir_exists(env_backup_path)) {
        printf("Backing up env folder...\n");
#ifdef _WIN32
        snprintf(backup_cmd, sizeof(backup_cmd), "move \"%s\" \"%s\"", env_path, env_backup_path);
#else
        snprintf(backup_cmd, sizeof(backup_cmd), "mv \"%s\" \"%s\"", env_path, env_backup_path);
#endif
        execute_command(backup_cmd);
    }

    if (dir_exists(project_name_path)) {
        char remove_cmd[STR_PATH_MAX + 64];
#ifdef _WIN32
        snprintf(remove_cmd, sizeof(remove_cmd), "rmdir /s /q \"%s\"", project_name_path);
#else
        snprintf(remove_cmd, sizeof(remove_cmd), "rm -rf \"%s\"", project_name_path);
#endif
        execute_command(remove_cmd);
    }

    printf("Extracting DIG Macro files...\n");
    snprintf(temp_extract_path, sizeof(temp_extract_path), "%s%stemp_extract", g_cwd, PATH_SEPARATOR);

#ifdef _WIN32
    snprintf(extract_cmd, sizeof(extract_cmd), "powershell -Command \"Expand-Archive -Path '%s' -DestinationPath '%s' -Force\"", project_zip_path, temp_extract_path);
#else
    snprintf(extract_cmd, sizeof(extract_cmd), "unzip -o \"%s\" -d \"%s\"", project_zip_path, temp_extract_path);
#endif

    if (execute_command(extract_cmd) != 0) {
        show_error("Failed to extract DIG Macro Source ZIP file.");
        remove(project_zip_path);
        exit(1);
        return 0;
    }

#ifdef _WIN32
    snprintf(move_cmd, sizeof(move_cmd), "powershell -Command \"Get-ChildItem -Path '%s\\*' | Move-Item -Destination '%s' -Force\"", temp_extract_path, project_name_path);
#else
    snprintf(move_cmd, sizeof(move_cmd),
        "mv \"%s\"/*/* \"%s\"/ 2>/dev/null || mv \"%s\"/* \"%s\"/ 2>/dev/null",
        temp_extract_path, project_name_path,
        temp_extract_path, project_name_path);
#endif
    
    execute_command(move_cmd);
    remove(project_zip_path);
    
#ifdef _WIN32
    snprintf(rm_cmd, sizeof(rm_cmd), "rmdir /s /q \"%s\"", temp_extract_path);
#else
    snprintf(rm_cmd, sizeof(rm_cmd), "rm -rf \"%s\"", temp_extract_path);
#endif
    execute_command(rm_cmd);

    if (!dir_exists(project_name_path)) {
        show_error("DIG Macro extraction failed. The project folder was not created correctly.");
        exit(1);
        return 0;
    }

    if (dir_exists(env_backup_path)) {
        printf("Importing env backup...\n");
#ifdef _WIN32
        snprintf(restore_cmd, sizeof(restore_cmd), "move \"%s\" \"%s\"", env_backup_path, env_path);
#else
        snprintf(restore_cmd, sizeof(restore_cmd), "mv \"%s\" \"%s\"", env_backup_path, env_path);
#endif
        execute_command(restore_cmd);
    }

    printf("DIG Macro extracted successfully.\n");
    return 1;
}

int install_digmacro(int force_update, const char *branch) {
    printf("Setting up DIG Macro...\n");

    char project_path[STR_PATH_MAX];
    snprintf(project_path, sizeof(project_path), "%s%s%s", g_cwd, PATH_SEPARATOR, PROJECT_NAME);

    if (dir_exists(project_path)) {
        if (force_update) {
            printf("Force update requested...\n");
            if (!download_and_extract(branch)) {
                printf("Failed to download and extract DIG Macro.\n");
                exit(1);
                return 0;
            }
        } else {
            printf("DIG Macro directory already exists. Use --update-source to force re-download.\n");
        }
    } else {
        if (!download_and_extract(branch)) {
            show_error("Failed to download and extract DIG Macro.\n");
            exit(1);
            return 0;
        }
    }

    return 1;
}

// ------------------- Launch ------------------- //

// ------------------- Kill Python Instances (macOS only) ------------------- //

int launch_digmacro(int argc, char *argv[], const char *python_cmd) {
    char env_folder[STR_PATH_MAX];
    char env_dev_folder[STR_PATH_MAX];
    char venv_folder[STR_PATH_MAX];
    char cmd[STR_PATH_MAX + 128];
    char venv_python[STR_PATH_MAX];
    char venv_python_tmp[STR_PATH_MAX];
    char launch_cmd[STR_PATH_MAX * 2];
    char project_name_path[STR_PATH_MAX];

    snprintf(project_name_path, sizeof(project_name_path), "%s%s%s", g_cwd, PATH_SEPARATOR, PROJECT_NAME);
    
#ifdef __APPLE__
    snprintf(env_folder, sizeof(env_folder), "%s%s%s%senv", g_cwd, PATH_SEPARATOR, PROJECT_NAME, PATH_SEPARATOR);
    snprintf(env_dev_folder, sizeof(env_dev_folder), "%s%sdev", env_folder, PATH_SEPARATOR);
    snprintf(venv_folder, sizeof(venv_folder), "%s%sDarwin", env_dev_folder, PATH_SEPARATOR);
#elif __linux__
    snprintf(env_folder, sizeof(env_folder), "%s%s%s%senv", g_cwd, PATH_SEPARATOR, PROJECT_NAME, PATH_SEPARATOR);
    snprintf(env_dev_folder, sizeof(env_dev_folder), "%s%sdev", env_folder, PATH_SEPARATOR);
    snprintf(venv_folder, sizeof(venv_folder), "%s%sLinux", env_dev_folder, PATH_SEPARATOR);
#elif _WIN32
    snprintf(env_folder, sizeof(env_folder), "%s%s%s%senv", g_cwd, PATH_SEPARATOR, PROJECT_NAME, PATH_SEPARATOR);
    snprintf(env_dev_folder, sizeof(env_dev_folder), "%s%sdev", env_folder, PATH_SEPARATOR);
    snprintf(venv_folder, sizeof(venv_folder), "%s%sWindows", env_dev_folder, PATH_SEPARATOR);
#endif
    
    make_dir(env_folder);
    make_dir(env_dev_folder);

    if (!dir_exists(venv_folder)) {
        printf("Creating virtual environment...\n");
        snprintf(cmd, sizeof(cmd), "%s -m venv \"%s\"", python_cmd, venv_folder);

        if (execute_command(cmd) != 0) {
            show_error("Failed to create virtual environment folder.\n");
            exit(1);
            return 0;
        }
    }

#if defined(__APPLE__) || defined(__linux__)
    snprintf(venv_python_tmp, sizeof(venv_python_tmp), "%s/bin/python3", venv_folder);
    if (get_realpath(venv_python_tmp, venv_python) != 0 || !file_exists(venv_python)) {
        show_error("Failed to find Python executable in virtual environment.");
        exit(1);
        return 0;
    }
#elif _WIN32
    snprintf(venv_python_tmp, sizeof(venv_python_tmp), "%s\\Scripts\\python.exe", venv_folder);
    if (get_realpath(venv_python_tmp, venv_python) != 0 || !file_exists(venv_python)) {
        show_error("Failed to find Python executable in virtual environment (try removing MSYS2/Git Bash Python from your PATH).");
        exit(1);
        return 0;
    }
#endif

#if defined(__APPLE__) || defined(__linux__)
    int pos = snprintf(launch_cmd, sizeof(launch_cmd), "%s \"%s/src/main.py\"", venv_python, project_name_path);
#elif _WIN32
    int pos = snprintf(launch_cmd, sizeof(launch_cmd), "%s \"%s\\src\\main.py\"", venv_python, project_name_path);
#endif

    for (int i = 0; i < argc; i++) {
        int remaining = sizeof(launch_cmd) - pos;
        if (remaining <= 10) {
            printf("Not enough space for more arguments\n");
            break;
        }

#ifdef _WIN32
        char escaped_arg[STR_PATH_MAX];
        char *src = argv[i];
        char *dst = escaped_arg;
        while (*src && (dst - escaped_arg) < sizeof(escaped_arg) - 2) {
            if (*src == '"') {
                *dst++ = '\\';
            }
            *dst++ = *src++;
        }
        *dst = '\0';
        
        int written = snprintf(launch_cmd + pos, remaining, " \"%s\"", escaped_arg);
#else
        char escaped_arg[STR_PATH_MAX];
        char *src = argv[i];
        char *dst = escaped_arg;

        while (*src && (dst - escaped_arg) < sizeof(escaped_arg) - 10) {
            if (*src == '\'') {
                strcpy(dst, "'\"'\"'");
                dst += 5;
            } else {
                *dst++ = *src;
            }
            src++;
        }
        *dst = '\0';
        
        int written = snprintf(launch_cmd + pos, remaining, " '%s'", escaped_arg);
#endif
        
        if (written < 0) {
            printf("snprintf failed\n");
            break;
        }
        if (written >= remaining) {
            printf("Argument truncated\n");
            break;
        }
        pos += written;
    }

    return execute_command(launch_cmd);
}

// ------------------- Main ------------------- //

int main(int argc, char *argv[]) {
    if (!get_executable_path(g_exe_path, sizeof(g_exe_path))) {
        show_error("Could not determine launcher path.\n");
        exit(1);
        return 0;
    }

#ifdef __APPLE__
    char real_path[STR_PATH_MAX];
    if (get_realpath(g_exe_path, real_path) == -1) {
        show_error("Could not resolve real application path.\n");
        exit(1);
        return 0;
    }

    // Contents/MacOS -> Contents -> .app
    // dirname(dirname(dirname(real_path)));

    char *app_dir = dirname(real_path);
    if (chdir(app_dir) != 0) {
        show_error("Could not change working directory.\n");
        exit(1);
        return 0;
    }
    
    setenv("DYLD_LIBRARY_PATH", "", 1);
    setenv("DYLD_FRAMEWORK_PATH", "", 1);
    
    if (strstr(real_path, ".app/Contents/MacOS/") != NULL) {
        printf("Running from app bundle - setting up environment for Python operations\n");
        setenv("PATH", "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin", 1);
        strcpy(g_exe_path, app_dir);
    }
#endif

    if (getcwd(g_cwd, sizeof(g_cwd)) == NULL) {
        show_error("Warning: Could not determine current directory.");
        exit(1);
        return 0;
    }

    printf("Launcher location: %s\n", g_exe_path);
    printf("Current directory: %s\n", g_cwd);

    printf("============ DIG Macro Launcher ============\n");
    
#ifdef _WIN32
    if (!check_path_windows()) {
        return 0;
    }
#elif defined(__linux__) || defined(__APPLE__)
    if (!check_path_posix()) {
        return 0;
    }
#endif

    printf("============ Checking Python ============\n");
    char python_cmd[STR_PATH_MAX];
    if (!check_python_version(python_cmd, sizeof(python_cmd))) {
        printf("Python 3.12.8 not found. Installing...\n");

#ifdef _WIN32
        if (!install_python_windows()) {
            show_error("Failed to install Python 3.12.8, exiting.\n");
            return 0;
        }
#elif __APPLE__
        if (!install_python_macos()) {
            show_error("Failed to install Python 3.12.8, exiting.\n");
            return 0;
        }
#else
        if (!install_python_unix()) {
            show_error("Failed to install Python 3.12.8, exiting.\n");
            return 0;
        }
#endif
        memset(python_cmd, 0, sizeof(python_cmd));
        if (!check_python_version(python_cmd, sizeof(python_cmd))) {
            show_error("Python 3.12.8 installation verification failed. Please install manually.\n");
            return 0;
        }
    }
    
    printf("\n============ Checking DIG Macro Files ============\n");
    const char *branch = get_branch_from_args(argc, argv);
    int force_update = 0;

    char **new_argv = malloc(argc * sizeof(char *));
    if (!new_argv) {
        perror("malloc");
        exit(1);
        return 0;
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
        return 0;
    }
    
    printf("\n============ Launching DIG Macro... ============\n");
    char **final_argv = malloc((new_argc + 2) * sizeof(char *));
    if (!final_argv) {
        perror("malloc");
        exit(1);
        return 0;
    }
    
    for (int i = 0; i < new_argc; i++) {
        final_argv[i] = new_argv[i];
    }
    
    char launcher_arg[2048];
    snprintf(launcher_arg, sizeof(launcher_arg), "--from-launcher=%s", g_exe_path);
    final_argv[new_argc] = strdup(launcher_arg);

    char cwd_arg[2048];
    char python_cwd[STR_PATH_MAX];

    snprintf(python_cwd, sizeof(python_cwd), "%s%s%s%ssrc", g_cwd, PATH_SEPARATOR, PROJECT_NAME, PATH_SEPARATOR);
    snprintf(cwd_arg, sizeof(cwd_arg), "--cwd=%s", python_cwd);
    final_argv[new_argc + 1] = strdup(cwd_arg);

    final_argv[new_argc + 2] = NULL;
    
    int result = launch_digmacro(new_argc + 2, final_argv, python_cmd);
    if (result != 0 && result != 9) {
        printf("\nDIG Macro exited with code: %d\n", result);
    }

    free(final_argv[new_argc]);
    free(final_argv[new_argc + 1]);
    free(final_argv);
    return result;
}