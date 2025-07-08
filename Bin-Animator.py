#!/usr/bin/python3
import subprocess
import os
import time
import threading
import datetime
import json
import sys

# --- Terminal/Logging Control ---
_is_interactive_session = os.isatty(sys.stdout.fileno())
_original_stdout = sys.stdout
_original_stderr = sys.stderr

# --- Configuration Loading ---
CONFIG_FILE_NAME = "config.json"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.path.join(SCRIPT_DIR, CONFIG_FILE_NAME)

config = {
    "check_interval_seconds": 60,
    "days_until_flies": 7,
    "paths": {
        "log_directory": "~/Documents",
        "pictures_directory": "~/Pictures",
        "trash_desktop_file_name": "Trash Can.desktop"
    },
    "icon_filenames": {
        "empty": "trash-empty.png",
        "full": "trash-full.png",
        "flies": "trash-flies.png"
    }
}

_global_log_file_path = os.path.join(os.path.expanduser("~/Documents"), "bin_animator_logs.txt")

def _write_to_log_file(message, level="INFO"):
    try:
        os.makedirs(os.path.dirname(_global_log_file_path), exist_ok=True)
        with open(_global_log_file_path, 'a') as f:
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{current_time}] [{level}] {message}\n")
    except IOError as e:
        _original_stderr.write(f"CRITICAL ERROR: Failed to write to log file '{_global_log_file_path}': {e}\n")
        _original_stderr.write(f"Original Message: [{level}] {message}\n")

def print_and_log(message, level="INFO"):
    if _is_interactive_session:
        _original_stdout.write(str(message) + '\n')
        _original_stdout.flush()
    _write_to_log_file(message, level)


try:
    with open(CONFIG_FILE_PATH, 'r') as f:
        loaded_config = json.load(f)
        for key, value in loaded_config.items():
            if key in config and isinstance(value, dict) and isinstance(config[key], dict):
                config[key].update(value)
            elif key in config:
                config[key] = value
    print_and_log(f"Configuration loaded successfully from {CONFIG_FILE_PATH}")
except FileNotFoundError:
    print_and_log(f"Warning: Configuration file '{CONFIG_FILE_NAME}' not found at '{CONFIG_FILE_PATH}'. Using default internal settings.", level="WARNING")
except json.JSONDecodeError as e:
    print_and_log(f"Error: Invalid JSON in '{CONFIG_FILE_NAME}': {e}. Using default internal settings. Please check your config file syntax.", level="ERROR")
except Exception as e:
    print_and_log(f"An unexpected error occurred while loading config: {e}. Using default internal settings.", level="ERROR")

# --- Set Global Log Path after config loads ---
LOG_DIRECTORY = os.path.expanduser(config["paths"]["log_directory"])
_global_log_file_path = os.path.join(LOG_DIRECTORY, "bin_animator_logs.txt")


CHECK_INTERVAL_SECONDS = config["check_interval_seconds"]
DAYS_UNTIL_FLIES = config["days_until_flies"]

# --- Path Definitions ---
TRASH_DIR_FILES = os.path.expanduser("~/.local/share/Trash/files/")

def expand_path(path):
    return os.path.expanduser(os.path.expandvars(path))

PICTURES_DIRECTORY = expand_path(config["paths"]["pictures_directory"])

ICON_EMPTY_FILENAME = config["icon_filenames"]["empty"]
ICON_FULL_FILENAME = config["icon_filenames"]["full"]
ICON_FLIES_FILENAME = config["icon_filenames"]["flies"]

ICON_EMPTY_PATH = os.path.join(PICTURES_DIRECTORY, ICON_EMPTY_FILENAME)
ICON_FULL_PATH = os.path.join(PICTURES_DIRECTORY, ICON_FULL_FILENAME)
ICON_FLIES_PATH = os.path.join(PICTURES_DIRECTORY, ICON_FLIES_FILENAME)

CUSTOM_DESKTOP_TRASH_FILE = os.path.expanduser(os.path.join("~/Desktop", config["paths"]["trash_desktop_file_name"]))

stop_monitoring_flag = threading.Event()


class TrashMonitor:
    def __init__(self):
        print_and_log("Initializing TrashMonitor...")
        os.makedirs(LOG_DIRECTORY, exist_ok=True)
        os.makedirs(PICTURES_DIRECTORY, exist_ok=True)

        if not os.path.exists(_global_log_file_path):
            print_and_log(f"Timestamp file not found. Creating {_global_log_file_path} with current timestamp.")
            self.set_last_empty_timestamp(ICON_EMPTY_PATH, initial_run=True)
        else:
            print_and_log(f"Timestamp file found: {_global_log_file_path}")

        self.create_desktop_launcher()
        self.update_desktop_icon()

        self.monitor_thread = threading.Thread(target=self.run_monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print_and_log("TrashMonitor initialized and monitoring thread started.")


    def create_desktop_launcher(self):
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={config["paths"]["trash_desktop_file_name"].replace('.desktop', '')}
Comment=Contains deleted files, monitored by custom script
Exec=xdg-open trash:///
Icon={ICON_EMPTY_PATH}
Terminal=false
StartupNotify=true
X-Trash-Monitor-Managed=true
"""
        try:
            with open(CUSTOM_DESKTOP_TRASH_FILE, 'w') as f:
                f.write(desktop_content)
            os.chmod(CUSTOM_DESKTOP_TRASH_FILE, 0o755)
            print_and_log(f"Created/updated desktop launcher: {CUSTOM_DESKTOP_TRASH_FILE}")
        except IOError as e:
            print_and_log(f"Error creating desktop launcher file '{CUSTOM_DESKTOP_TRASH_FILE}': {e}", level="ERROR")

    def update_desktop_icon_path_in_file(self, icon_path):
        try:
            with open(CUSTOM_DESKTOP_TRASH_FILE, 'r') as f:
                lines = f.readlines()

            updated_lines = []
            icon_changed = False
            for line in lines:
                if line.startswith("Icon="):
                    if line.strip() != f"Icon={icon_path}":
                        updated_lines.append(f"Icon={icon_path}\n")
                        icon_changed = True
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)

            if icon_changed:
                with open(CUSTOM_DESKTOP_TRASH_FILE, 'w') as f:
                    f.writelines(updated_lines)
                print_and_log(f"Desktop icon path updated to: {icon_path}")

        except FileNotFoundError:
            print_and_log(f"Error: Desktop launcher file not found at {CUSTOM_DESKTOP_TRASH_FILE}. Attempting to recreate.", level="ERROR")
            self.create_desktop_launcher()
            self.update_desktop_icon_path_in_file(icon_path)
        except Exception as e:
            print_and_log(f"Error updating desktop launcher icon for '{CUSTOM_DESKTOP_TRASH_FILE}': {e}", level="ERROR")

    def is_trash_empty(self):
        try:
            if not os.path.exists(TRASH_DIR_FILES):
                return True
            if not os.listdir(TRASH_DIR_FILES):
                return True
            return False
        except OSError as e:
            print_and_log(f"Error checking trash directory contents '{TRASH_DIR_FILES}': {e}", level="ERROR")
            return False

    def get_last_empty_timestamp(self):
        try:
            with open(_global_log_file_path, 'r') as f:
                lines = f.readlines()
                if len(lines) > 0:
                    timestamp_str = lines[0].strip()
                    if timestamp_str:
                        return datetime.datetime.fromtimestamp(float(timestamp_str))
                print_and_log(f"Warning: Timestamp file '{_global_log_file_path}' is empty or malformed. Treating as just emptied.", level="WARNING")
                return datetime.datetime.now()
        except (FileNotFoundError, ValueError) as e:
            print_and_log(f"Warning: Timestamp file '{_global_log_file_path}' not found or invalid format: {e}. Treating as just emptied.", level="WARNING")
            return datetime.datetime.now()
        except IOError as e:
            print_and_log(f"Error reading timestamp file '{_global_log_file_path}': {e}", level="ERROR")
            return datetime.datetime.now()


    def set_last_empty_timestamp(self, icon_path_for_log=None, initial_run=False):
        try:
            os.makedirs(os.path.dirname(_global_log_file_path), exist_ok=True)
            current_time = datetime.datetime.now()
            with open(_global_log_file_path, 'w') as f:
                f.write(str(current_time.timestamp()) + '\n')
            print_and_log(f"Timestamp updated in {_global_log_file_path} to {current_time.timestamp()}")
        except IOError as e:
            print_and_log(f"Critical error: Could not write timestamp to log file {_global_log_file_path}: {e}", level="CRITICAL")


    def update_desktop_icon(self):
        current_time = datetime.datetime.now()
        trash_is_empty = self.is_trash_empty()

        last_empty_dt = self.get_last_empty_timestamp()
        time_since_empty = current_time - last_empty_dt
        days_since_empty = time_since_empty.total_seconds() / (24 * 3600)

        icon_to_set = ICON_EMPTY_PATH

        if trash_is_empty:
            icon_to_set = ICON_EMPTY_PATH
            if (current_time - last_empty_dt).total_seconds() > CHECK_INTERVAL_SECONDS:
                self.set_last_empty_timestamp(ICON_EMPTY_PATH)
                print_and_log(f"Trash is empty. Updating log timestamp to current time.")
        else:
            if days_since_empty >= DAYS_UNTIL_FLIES:
                if os.path.exists(ICON_FLIES_PATH):
                    icon_to_set = ICON_FLIES_PATH
                    print_and_log(f"Trash is old ({days_since_empty:.2f} days). Setting to flies icon.")
                else:
                    print_and_log(f"Warning: Flies icon not found at {ICON_FLIES_PATH}. Using full icon as fallback.", level="WARNING")
                    icon_to_set = ICON_FULL_PATH
            else:
                if os.path.exists(ICON_FULL_PATH):
                    icon_to_set = ICON_FULL_PATH
                    print_and_log(f"Trash has contents ({days_since_empty:.2f} days old). Setting to full icon.")
                else:
                    print_and_log(f"Warning: Full icon not found at {ICON_FULL_PATH}. Using empty icon as fallback.", level="WARNING")
                    icon_to_set = ICON_EMPTY_PATH

        self.update_desktop_icon_path_in_file(icon_to_set)

    def run_monitor_loop(self):
        print_and_log("Monitoring loop started.")
        while not stop_monitoring_flag.is_set():
            self.update_desktop_icon()
            stop_monitoring_flag.wait(CHECK_INTERVAL_SECONDS)
        print_and_log("Monitoring loop stopped.")

# --- Main execution block ---
if __name__ == "__main__":
    print_and_log("Bin Animator script starting...")
    monitor = None
    try:
        monitor = TrashMonitor()
        if _is_interactive_session:
            print_and_log("Type 'stop' and press Enter to exit.")
            while True:
                user_input = input().strip().lower()
                if user_input == "stop":
                    print_and_log("Stop command received. Shutting down monitor...")
                    stop_monitoring_flag.set()
                    break
                else:
                    print_and_log("Unknown command. Type 'stop' to exit.")
        else:
            stop_monitoring_flag.wait()
            print_and_log("Stop signal received (external). Shutting down monitor.")

    except EOFError:
        print_and_log("\nEOF received (e.g., terminal closed). Shutting down monitor...", level="INFO")
        stop_monitoring_flag.set()
    except KeyboardInterrupt:
        print_and_log("\nKeyboardInterrupt received (Ctrl+C). Shutting down monitor...", level="INFO")
        stop_monitoring_flag.set()
    except Exception as e:
        print_and_log(f"CRITICAL ERROR (main thread): {e}", level="CRITICAL")
        import traceback
        _original_stderr.write(f"FATAL UNHANDLED EXCEPTION IN BIN-ANIMATOR. CHECK LOG FILE FOR DETAILS: {e}\n")
        _original_stderr.write(traceback.format_exc())

    finally:
        if monitor and monitor.monitor_thread.is_alive():
            print_and_log("Attempting to join monitoring thread...")
            monitor.monitor_thread.join(timeout=CHECK_INTERVAL_SECONDS + 5)
            if monitor.monitor_thread.is_alive():
                print_and_log("Warning: Monitoring thread did not terminate gracefully.", level="WARNING")
        print_and_log("Bin Animator has stopped.")