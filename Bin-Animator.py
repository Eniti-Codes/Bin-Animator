import subprocess
import os
import time
import threading
import datetime

# --- Configuration ---
CHECK_INTERVAL_SECONDS = 60 # Check every 60 seconds (1 minute)

# Threshold for 'flies' icon (in days)
DAYS_UNTIL_FLIES = 7 # Flies after 7 days



TRASH_DIR_FILES = os.path.expanduser("~/.local/share/Trash/files/")

# --- Log File Path ---
def get_documents_dir():
    documents_dir = os.environ.get('XDG_DOCUMENTS_DIR')
    if documents_dir:
        return os.path.expanduser(documents_dir)
    else:
        return os.path.expanduser("~/Documents")

DOCUMENTS_DIR = get_documents_dir()
LAST_EMPTY_TIMESTAMP_FILE = os.path.join(DOCUMENTS_DIR, "bin_animator_logs.txt")

# --- Icon Paths ---
def get_pictures_dir():
    pictures_dir = os.environ.get('XDG_PICTURES_DIR')
    if pictures_dir:
        return os.path.expanduser(pictures_dir)
    else:
        return os.path.expanduser("~/Pictures")

PICTURES_DIR = get_pictures_dir()

ICON_EMPTY_FILENAME = "trash-empty.png"
ICON_FULL_FILENAME = "trash-full.png"
ICON_FLIES_FILENAME = "trash-flies.png"

ICON_EMPTY_PATH = os.path.join(PICTURES_DIR, ICON_EMPTY_FILENAME)
ICON_FULL_PATH = os.path.join(PICTURES_DIR, ICON_FULL_FILENAME)
ICON_FLIES_PATH = os.path.join(PICTURES_DIR, ICON_FLIES_FILENAME)

CUSTOM_DESKTOP_TRASH_FILE = os.path.expanduser("~/Desktop/MyTrash.desktop")


stop_monitoring_flag = threading.Event()


class TrashMonitor:
    def __init__(self):
        os.makedirs(DOCUMENTS_DIR, exist_ok=True)
        os.makedirs(PICTURES_DIR, exist_ok=True)


        if not os.path.exists(LAST_EMPTY_TIMESTAMP_FILE):
            print(f"Log file not found. Creating {LAST_EMPTY_TIMESTAMP_FILE} with current timestamp.")
            self.set_last_empty_timestamp(ICON_EMPTY_PATH, initial_run=True)
        else:
            print(f"Log file found: {LAST_EMPTY_TIMESTAMP_FILE}")

        self.create_desktop_launcher()
        self.update_desktop_icon()

        self.monitor_thread = threading.Thread(target=self.run_monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def create_desktop_launcher(self):
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=My Trash Can
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
            print(f"Created/updated desktop launcher: {CUSTOM_DESKTOP_TRASH_FILE}")
        except IOError as e:
            print(f"Error creating desktop launcher file: {e}")

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
                print(f"Desktop icon path updated to: {icon_path}")
                # Log the icon path update
                self.log_icon_update(icon_path)

        except FileNotFoundError:
            print(f"Error: Desktop launcher file not found at {CUSTOM_DESKTOP_TRASH_FILE}. Recreating.")
            self.create_desktop_launcher()
            self.update_desktop_icon_path_in_file(icon_path)
        except Exception as e:
            print(f"Error updating desktop launcher icon: {e}")

    def is_trash_empty(self):
        try:
            if not os.path.exists(TRASH_DIR_FILES):
                return True
            if not os.listdir(TRASH_DIR_FILES):
                return True
            return False
        except OSError as e:
            print(f"Error checking trash directory contents: {e}")
            return False

    def get_last_empty_timestamp(self):
        try:
            with open(LAST_EMPTY_TIMESTAMP_FILE, 'r') as f:
                lines = f.readlines()
                if len(lines) > 0:
                    timestamp_str = lines[0].strip()
                    if timestamp_str:
                        return datetime.datetime.fromtimestamp(float(timestamp_str))
        
                return datetime.datetime.now()
        except (FileNotFoundError, ValueError):
            return datetime.datetime.now()
        except IOError as e:
            print(f"Error reading timestamp file: {e}")
            return datetime.datetime.now()


    def set_last_empty_timestamp(self, icon_path_for_log=None, initial_run=False):
        """
        Updates the log file with the current timestamp and optionally the icon path.
        `initial_run` is used to prevent logging icon update if called during __init__
        """
        try:
            os.makedirs(os.path.dirname(LAST_EMPTY_TIMESTAMP_FILE), exist_ok=True)
            current_time = datetime.datetime.now()
            with open(LAST_EMPTY_TIMESTAMP_FILE, 'w') as f:
                f.write(str(current_time.timestamp()) + '\n')
                if icon_path_for_log and not initial_run:
                    f.write(f"Icon updated to: {icon_path_for_log} at {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        except IOError as e:
            print(f"Error writing timestamp file: {e}")

    def log_icon_update(self, icon_path):
        """Appends the icon path update to the log file."""
        try:
            with open(LAST_EMPTY_TIMESTAMP_FILE, 'a') as f:
                current_time = datetime.datetime.now()
                f.write(f"Icon updated to: {icon_path} at {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        except IOError as e:
            print(f"Error appending icon update to log file: {e}")


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
                print(f"Trash is empty. Updating log timestamp to current time.")
        else:
            if days_since_empty >= DAYS_UNTIL_FLIES:
                if os.path.exists(ICON_FLIES_PATH):
                    icon_to_set = ICON_FLIES_PATH
                    print(f"Trash is old ({days_since_empty:.2f} days). Setting to flies icon.")
                else:
                    print(f"Warning: Flies icon not found at {ICON_FLIES_PATH}. Using full icon as fallback.")
                    icon_to_set = ICON_FULL_PATH
            else:
                if os.path.exists(ICON_FULL_PATH):
                    icon_to_set = ICON_FULL_PATH
                    print(f"Trash has contents ({days_since_empty:.2f} days old). Setting to full icon.")
                else:
                    print(f"Warning: Full icon not found at {ICON_FULL_PATH}. Using empty icon as fallback.")
                    icon_to_set = ICON_EMPTY_PATH

        self.update_desktop_icon_path_in_file(icon_to_set)

    def run_monitor_loop(self):
        while not stop_monitoring_flag.is_set():
            self.update_desktop_icon()
            stop_monitoring_flag.wait(CHECK_INTERVAL_SECONDS)

# ___ Main execution block ___
if __name__ == "__main__":
    print("Starting desktop trash monitor...")
    print("Type 'stop' and press Enter to exit.")
    monitor = TrashMonitor()
    try:
        while True:
            user_input = input().strip().lower()
            if user_input == "stop":
                print("Stop command received. Shutting down monitor...")
                stop_monitoring_flag.set()
                break
            else:
                print("Unknown command. Type 'stop' to exit.")
    except EOFError:
        print("\nEOF received. Shutting down monitor...")
        stop_monitoring_flag.set()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Shutting down monitor...")
        stop_monitoring_flag.set()
    except Exception as e:
        print(f"An unexpected error occurred in the main thread: {e}")

    if monitor.monitor_thread.is_alive():
        monitor.monitor_thread.join(timeout=CHECK_INTERVAL_SECONDS + 2)
        if monitor.monitor_thread.is_alive():
            print("Warning: Monitoring thread did not terminate gracefully.")
    print("Bin Animator has stopped.")