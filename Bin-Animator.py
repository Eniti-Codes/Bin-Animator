#!/usr/bin/python3
import subprocess
import os
import time
import threading
import datetime
import json
import sys


# --- Global logging function (will write to the dedicated log file) ---
_log_file_path_global = None

def _log_message_to_dedicated_file(message, level="INFO"):
    """
    Writes a message directly to the dedicated log file.
    Includes a fallback to sys.stderr for critical failures to write to the log file.
    """
    log_path = _log_file_path_global if _log_file_path_global else \
               os.path.join(os.path.expanduser("~/Documents"), "bin_animator_logs.txt")

    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a') as f:
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{current_time}] [{level}] {message}\n")
    except IOError as e:
        sys.stderr.write(f"CRITICAL LOGGING ERROR: Could not write to dedicated log file '{log_path}': {e}\n")
        sys.stderr.write(f"Original message: [{level}] {message}\n")


# --- Configuration Loading ---
CONFIG_FILE_NAME = "config.json"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.path.join(SCRIPT_DIR, CONFIG_FILE_NAME)

# Default configuration values
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

try:
    with open(CONFIG_FILE_PATH, 'r') as f:
        loaded_config = json.load(f)
        for key, value in loaded_config.items():
            if key in config and isinstance(value, dict) and isinstance(config[key], dict):
                config[key].update(value)
            elif key in config:
                config[key] = value
    _log_message_to_dedicated_file(f"Configuration loaded successfully from {CONFIG_FILE_PATH}")
except FileNotFoundError:
    _log_message_to_dedicated_file(f"Warning: Configuration file '{CONFIG_FILE_NAME}' not found at '{CONFIG_FILE_PATH}'. Using default internal settings.", level="WARNING")
except json.JSONDecodeError as e:
    _log_message_to_dedicated_file(f"Error: Invalid JSON in '{CONFIG_FILE_NAME}': {e}. Using default internal settings. Please check your config file syntax.", level="ERROR")
except Exception as e:
    _log_message_to_dedicated_file(f"An unexpected error occurred while loading config: {e}. Using default internal settings.", level="ERROR")


# --- Path Definitions (using configured values) ---
TRASH_DIR_FILES = os.path.expanduser("~/.local/share/Trash/files/")

def expand_path(path):
    """Helper to expand user and environment variables in a path."""
    return os.path.expanduser(os.path.expandvars(path))

LOG_DIRECTORY = expand_path(config["paths"]["log_directory"])
LAST_EMPTY_TIMESTAMP_FILE = os.path.join(LOG_DIRECTORY, "bin_animator_logs.txt")
_log_file_path_global = LAST_EMPTY_TIMESTAMP_FILE

CHECK_INTERVAL_SECONDS = config["check_interval_seconds"]
DAYS_UNTIL_FLIES = config["days_until_flies"]


# --- Icon Paths ---
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
        _log_message_to_dedicated_file("Initializing TrashMonitor...")
        os.makedirs(LOG_DIRECTORY, exist_ok=True)
        os.makedirs(PICTURES_DIRECTORY, exist_ok=True)

        if not os.path.exists(LAST_EMPTY_TIMESTAMP_FILE):
            _log_message_to_dedicated_file(f"Timestamp file not found. Creating {LAST_EMPTY_TIMESTAMP_FILE} with current timestamp.")
            self.set_last_empty_timestamp(ICON_EMPTY_PATH, initial_run=True)
        else:
            _log_message_to_dedicated_file(f"Timestamp file found: {LAST_EMPTY_TIMESTAMP_FILE}")

        self.create_desktop_launcher()
        self.update_desktop_icon()

        self.monitor_thread = threading.Thread(target=self.run_monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        _log_message_to_dedicated_file("TrashMonitor initialized and monitoring thread started.")


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
            _log_message_to_dedicated_file(f"Created/updated desktop launcher: {CUSTOM_DESKTOP_TRASH_FILE}")
        except IOError as e:
            _log_message_to_dedicated_file(f"Error creating desktop launcher file '{CUSTOM_DESKTOP_TRASH_FILE}': {e}", level="ERROR")

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
                _log_message_to_dedicated_file(f"Desktop icon path updated to: {icon_path}")

        except FileNotFoundError:
            _log_message_to_dedicated_file(f"Error: Desktop launcher file not found at {CUSTOM_DESKTOP_TRASH_FILE}. Attempting to recreate.", level="ERROR")
            self.create_desktop_launcher()
            self.update_desktop_icon_path_in_file(icon_path)
        except Exception as e:
            _log_message_to_dedicated_file(f"Error updating desktop launcher icon for '{CUSTOM_DESKTOP_TRASH_FILE}': {e}", level="ERROR")

    def is_trash_empty(self):
        try:
            if not os.path.exists(TRASH_DIR_FILES):
                return True
            if not os.listdir(TRASH_DIR_FILES):
                return True
            return False
        except OSError as e:
            _log_message_to_dedicated_file(f"Error checking trash directory contents '{TRASH_DIR_FILES}': {e}", level="ERROR")
            return False

    def get_last_empty_timestamp(self):
        try:
            with open(LAST_EMPTY_TIMESTAMP_FILE, 'r') as f:
                lines = f.readlines()
                if len(lines) > 0:
                    timestamp_str = lines[0].strip()
                    if timestamp_str:
                        return datetime.datetime.fromtimestamp(float(timestamp_str))
                _log_message_to_dedicated_file(f"Warning: Timestamp file '{LAST_EMPTY_TIMESTAMP_FILE}' is empty or malformed. Treating as just emptied.", level="WARNING")
                return datetime.datetime.now()
        except (FileNotFoundError, ValueError) as e:
            _log_message_to_dedicated_file(f"Warning: Timestamp file '{LAST_EMPTY_TIMESTAMP_FILE}' not found or invalid format: {e}. Treating as just emptied.", level="WARNING")
            return datetime.datetime.now()
        except IOError as e:
            _log_message_to_dedicated_file(f"Error reading timestamp file '{LAST_EMPTY_TIMESTAMP_FILE}': {e}", level="ERROR")
            return datetime.datetime.now()


    def set_last_empty_timestamp(self, icon_path_for_log=None, initial_run=False):
        """
        Updates the first line of the log file with the current timestamp.
        """
        try:
            os.makedirs(os.path.dirname(LAST_EMPTY_TIMESTAMP_FILE), exist_ok=True)
            current_time = datetime.datetime.now()
            with open(LAST_EMPTY_TIMESTAMP_FILE, 'w') as f:
                f.write(str(current_time.timestamp()) + '\n')
            _log_message_to_dedicated_file(f"Timestamp updated in {LAST_EMPTY_TIMESTAMP_FILE} to {current_time.timestamp()}")
        except IOError as e:
            _log_message_to_dedicated_file(f"Critical error: Could not write timestamp to log file {LAST_EMPTY_TIMESTAMP_FILE}: {e}", level="CRITICAL")


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
                _log_message_to_dedicated_file(f"Trash is empty. Updating log timestamp to current time.")
        else:
            if days_since_empty >= DAYS_UNTIL_FLIES:
                if os.path.exists(ICON_FLIES_PATH):
                    icon_to_set = ICON_FLIES_PATH
                    _log_message_to_dedicated_file(f"Trash is old ({days_since_empty:.2f} days). Setting to flies icon.")
                else:
                    _log_message_to_dedicated_file(f"Warning: Flies icon not found at {ICON_FLIES_PATH}. Using full icon as fallback.", level="WARNING")
                    icon_to_set = ICON_FULL_PATH
            else:
                # Trash is not empty but NOT old enough for flies
                if os.path.exists(ICON_FULL_PATH):
                    icon_to_set = ICON_FULL_PATH
                    _log_message_to_dedicated_file(f"Trash has contents ({days_since_empty:.2f} days old). Setting to full icon.")
                else:
                    _log_message_to_dedicated_file(f"Warning: Full icon not found at {ICON_FULL_PATH}. Using empty icon as fallback.", level="WARNING")
                    icon_to_set = ICON_EMPTY_PATH

        self.update_desktop_icon_path_in_file(icon_to_set)

    def run_monitor_loop(self):
        _log_message_to_dedicated_file("Monitoring loop started.")
        while not stop_monitoring_flag.is_set():
            self.update_desktop_icon()
            stop_monitoring_flag.wait(CHECK_INTERVAL_SECONDS)
        _log_message_to_dedicated_file("Monitoring loop stopped.")


# --- Main execution block ---
if __name__ == "__main__":
    _log_message_to_dedicated_file("Bin Animator script starting...")
    monitor = None
    try:
        monitor = TrashMonitor()
        stop_monitoring_flag.wait()
        _log_message_to_dedicated_file("Stop signal received. Shutting down monitor.")

    except Exception as e:
        _log_message_to_dedicated_file(f"CRITICAL ERROR (main thread): {e}", level="CRITICAL")
        import traceback
        _log_message_to_dedicated_file(f"Full traceback for critical error:\n{traceback.format_exc()}", level="CRITICAL")
        sys.stderr.write(f"FATAL UNHANDLED EXCEPTION IN BIN-ANIMATOR. CHECK LOG FILE FOR DETAILS: {e}\n")
        sys.stderr.write(traceback.format_exc())

    finally:
        if monitor and monitor.monitor_thread.is_alive():
            _log_message_to_dedicated_file("Attempting to join monitoring thread...")
            monitor.monitor_thread.join(timeout=CHECK_INTERVAL_SECONDS + 5)
            if monitor.monitor_thread.is_alive():
                _log_message_to_dedicated_file("Warning: Monitoring thread did not terminate gracefully.", level="WARNING")
        _log_message_to_dedicated_file("Bin Animator has stopped.")