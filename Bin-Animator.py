#!/usr/bin/python3

# Bin Animator - visually remind you to empty your bin based on how long items have been sitting there.
#
# Copyright (C) 2025 Eniti-Codes
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.



import subprocess
import os
import time
import threading
import datetime
import json
import sys
import glob

_is_interactive_session = os.isatty(sys.stdout.fileno())
_original_stdout = sys.stdout
_original_stderr = sys.stderr

CONFIG_FILE_NAME = "config.json"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.path.join(SCRIPT_DIR, CONFIG_FILE_NAME)

config = {
    "check_interval_seconds": 60,
    "days_until_flies": 7,
    "paths": {
        "log_directory": "",
        "pictures_directory": "",
        "trash_desktop_file_name": ""
    },
    "icon_filenames": {},
    "enable_animation": False,
    "animation_interval_seconds": 0.5,
    "enable_notification": False,
    "notification_message": "Your Bin hasn't been emptied in over {days} days!"
}

# --- Utility Function: Logging ---
ENABLE_FILE_LOGGING = False 
_global_log_file_path = ""

def _write_to_log_file(message, level="INFO"):
    global _global_log_file_path
    
    if not ENABLE_FILE_LOGGING:
        return

    try:
        if not _global_log_file_path:
             return 
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

# --- CRITICAL VALIDATION FUNCTION ---
def validate_and_setup_config():
    global ENABLE_FILE_LOGGING, _global_log_file_path, PICTURES_DIRECTORY
    
    CRITICAL_PATHS = ["pictures_directory", "trash_desktop_file_name"]
    CRITICAL_ICONS = ["empty", "full", "flies"]
    
    for key in CRITICAL_PATHS:
        path = config["paths"].get(key, "").strip()
        if not path:
            print_and_log(f"CRITICAL ERROR: Required configuration value 'paths.{key}' is missing or empty. Script cannot run.", level="CRITICAL")
            return False
    
    for key in CRITICAL_ICONS:
        if not config["icon_filenames"].get(key, "").strip():
            print_and_log(f"CRITICAL ERROR: Required configuration value 'icon_filenames.{key}' is missing or empty. Script cannot run.", level="CRITICAL")
            return False

    log_directory_raw = config["paths"].get("log_directory", "").strip()
    if log_directory_raw:
        ENABLE_FILE_LOGGING = True
        LOG_DIRECTORY = os.path.expanduser(log_directory_raw)
        _global_log_file_path = os.path.join(LOG_DIRECTORY, "bin_animator_logs.txt")
        print_and_log(f"File logging is ENABLED. Log path: {_global_log_file_path}")
    else:
        ENABLE_FILE_LOGGING = False
        print_and_log("File logging is DISABLED (Empty log directory path). Logs will only go to standard output.")
        
    def expand_path(path):
        return os.path.expanduser(os.path.expandvars(path))
        
    PICTURES_DIRECTORY = expand_path(config["paths"]["pictures_directory"])
    return True

# Load configuration from file
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
    print_and_log(f"CRITICAL ERROR: Configuration file '{CONFIG_FILE_NAME}' not found at '{CONFIG_FILE_PATH}'. Script cannot run.", level="CRITICAL")
    sys.exit(1)
except json.JSONDecodeError as e:
    print_and_log(f"CRITICAL ERROR: Invalid JSON in '{CONFIG_FILE_NAME}': {e}. Script cannot run. Please check file syntax.", level="CRITICAL")
    sys.exit(1)
except Exception as e:
    print_and_log(f"CRITICAL ERROR: An unexpected error occurred while loading config: {e}. Script cannot run.", level="CRITICAL")
    sys.exit(1)

# Run Validation
if not validate_and_setup_config():
    sys.exit(1)

# --- Set Global Variables after config loads and validation ---
CHECK_INTERVAL_SECONDS = config["check_interval_seconds"]
DAYS_UNTIL_FLIES = config["days_until_flies"]

# --- Path Definitions ---
TRASH_DIR_FILES = os.path.expanduser("~/.local/share/Trash/files/")

ICON_EMPTY_FILENAME = config["icon_filenames"]["empty"]
ICON_FULL_FILENAME = config["icon_filenames"]["full"]
ICON_FLIES_FILENAME = config["icon_filenames"]["flies"]
ICON_EMPTY_PATH = os.path.join(PICTURES_DIRECTORY, ICON_EMPTY_FILENAME)
ICON_FULL_PATH = os.path.join(PICTURES_DIRECTORY, ICON_FULL_FILENAME)
ICON_FLIES_PATH = os.path.join(PICTURES_DIRECTORY, ICON_FLIES_FILENAME)

ENABLE_ANIMATION = config["enable_animation"]
ANIMATION_INTERVAL = config["animation_interval_seconds"]

ENABLE_NOTIFICATION = config["enable_notification"]
NOTIFICATION_MESSAGE = config["notification_message"]

CUSTOM_DESKTOP_TRASH_FILE = os.path.expanduser(os.path.join("~/Desktop", config["paths"]["trash_desktop_file_name"]))
stop_monitoring_flag = threading.Event()
animation_stop_flag = threading.Event()

class AnimationThread(threading.Thread):
    def __init__(self, monitor_ref, icon_paths):
        super().__init__()
        self.monitor = monitor_ref
        self.icon_paths = icon_paths
        self.daemon = True
        self.current_frame = 0
        self.is_running = False

    def run(self):
        self.is_running = True
        print_and_log("Animation thread started.")
        while not animation_stop_flag.is_set() and self.is_running:
            if not self.icon_paths:
                print_and_log("Warning: Animation frames list is empty. Stopping animation.", level="WARNING")
                break
            
            icon_path = self.icon_paths[self.current_frame % len(self.icon_paths)]
            self.monitor.update_desktop_icon_path_in_file(icon_path, log_change=False) 
            self.current_frame += 1
            animation_stop_flag.wait(ANIMATION_INTERVAL)
        print_and_log("Animation thread stopped.")
    
    def stop(self):
        self.is_running = False

class TrashMonitor:
    def __init__(self):
        print_and_log("Initializing TrashMonitor...")
        
        if ENABLE_FILE_LOGGING:
            os.makedirs(os.path.dirname(_global_log_file_path), exist_ok=True)
            
        os.makedirs(PICTURES_DIRECTORY, exist_ok=True)
        
        self.animation_frames = self.find_animation_frames()
        self.animation_thread = None
        self.is_animating = False
        self.notification_sent_since_last_full = False
        
        if ENABLE_FILE_LOGGING:
            if not os.path.exists(_global_log_file_path):
                print_and_log(f"Timestamp file not found. Creating {_global_log_file_path} with current timestamp.")
                self.set_last_empty_timestamp(initial_run=True)
            else:
                print_and_log(f"Timestamp file found: {_global_log_file_path}")
            
        self.create_desktop_launcher()
        self.update_desktop_icon()
        
        self.monitor_thread = threading.Thread(target=self.run_monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print_and_log("TrashMonitor initialized and monitoring thread started.")

    def find_animation_frames(self):
        frames = []
        frame_keys = [k for k in config["icon_filenames"] if k.strip().lower().startswith("frame")]
        
        def sort_key(key):
            try:
                num_part = ''.join(filter(str.isdigit, key))
                return int(num_part) if num_part else float('inf')
            except ValueError:
                return float('inf')

        sorted_frame_keys = sorted(frame_keys, key=sort_key)
        
        for key in sorted_frame_keys:
            filename = config["icon_filenames"][key]
            full_path = os.path.join(PICTURES_DIRECTORY, filename)
            if os.path.exists(full_path):
                frames.append(full_path)
        
        if frames:
            print_and_log(f"Found {len(frames)} animation frames defined in config.")
        return frames

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
            
    def update_desktop_icon_path_in_file(self, icon_path, log_change=True):
        if not icon_path: return 

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
                if log_change:
                    print_and_log(f"Desktop icon path updated to: {icon_path}")
                subprocess.run(["touch", CUSTOM_DESKTOP_TRASH_FILE], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
        except FileNotFoundError:
            print_and_log(f"Error: Desktop launcher file not found at {CUSTOM_DESKTOP_TRASH_FILE}. Attempting to recreate.", level="ERROR")
            self.create_desktop_launcher()
            self.update_desktop_icon_path_in_file(icon_path)
        except Exception as e:
            print_and_log(f"Error updating desktop launcher icon for '{CUSTOM_DESKTOP_TRASH_FILE}': {e}", level="ERROR")

    # (is_trash_empty)
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
        if not ENABLE_FILE_LOGGING:
            return datetime.datetime.now()
            
        try:
            with open(_global_log_file_path, 'r') as f:
                lines = f.readlines()
            if lines and lines[0].strip():
                return datetime.datetime.fromtimestamp(float(lines[0].strip()))
            
            print_and_log(f"Warning: Timestamp file '{_global_log_file_path}' is empty or malformed. Treating as just emptied.", level="WARNING")
            return datetime.datetime.now()
        except Exception as e:
            print_and_log(f"Warning: Error reading timestamp file: {e}. Treating as just emptied.", level="WARNING")
            return datetime.datetime.now()
            
    def set_last_empty_timestamp(self, initial_run=False):
        if not ENABLE_FILE_LOGGING:
            return
            
        try:
            os.makedirs(os.path.dirname(_global_log_file_path), exist_ok=True)
            current_time = datetime.datetime.now()
            with open(_global_log_file_path, 'w') as f:
                f.write(str(current_time.timestamp()) + '\n')
            print_and_log(f"Timestamp updated in {_global_log_file_path} to {current_time.timestamp()}")
        except IOError as e:
            print_and_log(f"Critical error: Could not write timestamp to log file {_global_log_file_path}: {e}", level="CRITICAL")

    # (send_notification)
    def send_notification(self, title, message):
        try:
            subprocess.run(["notify-send", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            subprocess.run([
                "notify-send", 
                "--icon", ICON_FULL_PATH, 
                title, 
                message
            ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print_and_log(f"Sent notification: {title} - {message}")
            self.notification_sent_since_last_full = True
            
        except FileNotFoundError:
            print_and_log("Warning: 'notify-send' command not found. Cannot send desktop notifications.", level="WARNING")
        except Exception as e:
            print_and_log(f"Error sending notification: {e}", level="ERROR")

    # (update_desktop_icon)
    def update_desktop_icon(self):
        current_time = datetime.datetime.now()
        trash_is_empty = self.is_trash_empty()
        last_empty_dt = self.get_last_empty_timestamp()
        time_since_empty = current_time - last_empty_dt
        days_since_empty = time_since_empty.total_seconds() / (24 * 3600)
        
        icon_to_set = ICON_EMPTY_PATH
        
        # --- Handle Empty Trash State ---
        if trash_is_empty:
            if self.is_animating:
                animation_stop_flag.set()
                if self.animation_thread and self.animation_thread.is_alive():
                    self.animation_thread.join(timeout=1)
                self.is_animating = False
                animation_stop_flag.clear()
                print_and_log("Animation stopped (Trash is empty).")

            if (current_time - last_empty_dt).total_seconds() > CHECK_INTERVAL_SECONDS:
                self.set_last_empty_timestamp()
                print_and_log("Trash is empty. Updating log timestamp to current time.")
            
            icon_to_set = ICON_EMPTY_PATH
            self.notification_sent_since_last_full = False 
            
        else:
            if days_since_empty >= DAYS_UNTIL_FLIES:
                state_message = f"Trash is OLD ({days_since_empty:.2f} days). Flies state activated."
                
                if ENABLE_ANIMATION and self.animation_frames:
                    if not self.is_animating:
                        self.animation_thread = AnimationThread(self, self.animation_frames)
                        self.animation_thread.start()
                        self.is_animating = True
                        print_and_log("Animation started (Flies state).")
                    
                else:
                    if self.is_animating:
                        animation_stop_flag.set()
                        if self.animation_thread and self.animation_thread.is_alive():
                            self.animation_thread.join(timeout=1)
                        self.is_animating = False
                        animation_stop_flag.clear()
                        print_and_log("Animation stopped (Flies state, animation disabled/missing).")
                        
                    if os.path.exists(ICON_FLIES_PATH):
                        icon_to_set = ICON_FLIES_PATH
                    else:
                        print_and_log(f"Warning: Flies icon not found at {ICON_FLIES_PATH}. Using full icon as fallback.", level="WARNING")
                        icon_to_set = ICON_FULL_PATH
                
                # Check for Notification
                if ENABLE_NOTIFICATION and not self.notification_sent_since_last_full:
                    title = "Bin Animator Alert!"
                    message = NOTIFICATION_MESSAGE.format(days=DAYS_UNTIL_FLIES)
                    self.send_notification(title, message)
                    
            else:
                state_message = f"Trash has contents ({days_since_empty:.2f} days old). Setting to full icon."
                
                if self.is_animating:
                    animation_stop_flag.set()
                    if self.animation_thread and self.animation_thread.is_alive():
                        self.animation_thread.join(timeout=1)
                    self.is_animating = False
                    animation_stop_flag.clear()
                    print_and_log("Animation stopped (Full state, not old enough).")
                    
                if os.path.exists(ICON_FULL_PATH):
                    icon_to_set = ICON_FULL_PATH
                else:
                    print_and_log(f"Warning: Full icon not found at {ICON_FULL_PATH}. Using empty icon as fallback.", level="WARNING")
                    icon_to_set = ICON_EMPTY_PATH
            
            print_and_log(state_message)
            
        if not self.is_animating and icon_to_set:
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
        # Check if we exited early from config validation
        if not 'PICTURES_DIRECTORY' in locals() or not 'PICTURES_DIRECTORY' in globals():
            print_and_log("Initialization failed due to critical configuration errors.", level="CRITICAL")
            sys.exit(1)
            
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
    except Exception as e:
        print_and_log(f"CRITICAL ERROR (main thread): {e}", level="CRITICAL")
        import traceback
        _original_stderr.write(f"FATAL UNHANDLED EXCEPTION IN BIN-ANIMATOR. CHECK LOG FILE FOR DETAILS: {e}\n")
        _original_stderr.write(traceback.format_exc())
    finally:
        animation_stop_flag.set()
        if monitor and monitor.is_animating and monitor.animation_thread:
            print_and_log("Attempting to join animation thread...")
            monitor.animation_thread.join(timeout=ANIMATION_INTERVAL + 1)

        if monitor and monitor.monitor_thread and monitor.monitor_thread.is_alive():
            print_and_log("Attempting to join main monitoring thread...")
            monitor.monitor_thread.join(timeout=CHECK_INTERVAL_SECONDS + 5)
        
        print_and_log("Bin Animator has stopped.")
