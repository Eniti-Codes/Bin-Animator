import subprocess
import os
import time
import threading
import datetime
# No gi.repository imports needed as we are not using GTK/AppIndicator UI

# --- Configuration ---
# How often to check the trash (in seconds)
CHECK_INTERVAL_SECONDS = 60 # Check every 60 seconds (1 minute)

# Path to the user's trash directory (where deleted files are)
TRASH_DIR_FILES = os.path.expanduser("~/.local/share/Trash/files/")

# --- Log File Path ---
# Dynamically find the user's Documents directory
def get_documents_dir():
    documents_dir = os.environ.get('XDG_DOCUMENTS_DIR')
    if documents_dir:
        return os.path.expanduser(documents_dir)
    else:
        return os.path.expanduser("~/Documents")

DOCUMENTS_DIR = get_documents_dir()

# File to store the timestamp of the last trash empty event
LAST_EMPTY_TIMESTAMP_FILE = os.path.join(DOCUMENTS_DIR, "trash_monitor_last_empty_log.txt")

# Threshold for 'flies' icon (in days)
DAYS_UNTIL_FLIES = 7

# --- Icon Paths ---
# Dynamically find the user's Pictures directory
def get_pictures_dir():
    pictures_dir = os.environ.get('XDG_PICTURES_DIR')
    if pictures_dir:
        return os.path.expanduser(pictures_dir)
    else:
        return os.path.expanduser("~/Pictures")

PICTURES_DIR = get_pictures_dir()

# Specific filenames for custom icons (must be in PICTURES_DIR)
ICON_EMPTY_FILENAME = "trash-empty.png"
ICON_FLIES_FILENAME = "trash-flies.png"

ICON_EMPTY_PATH = os.path.join(PICTURES_DIR, ICON_EMPTY_FILENAME)
ICON_FLIES_PATH = os.path.join(PICTURES_DIR, ICON_FLIES_FILENAME)

# Path for the custom desktop launcher file
CUSTOM_DESKTOP_TRASH_FILE = os.path.expanduser("~/Desktop/MyTrash.desktop")

class TrashMonitor:
    def __init__(self):
        # Ensure necessary directories exist
        os.makedirs(DOCUMENTS_DIR, exist_ok=True)
        os.makedirs(PICTURES_DIR, exist_ok=True)

        self.create_desktop_launcher() # Create or update the .desktop file initially
        self.update_desktop_icon() # Perform initial icon update

        # Start a separate thread for continuous monitoring
        self.monitor_thread = threading.Thread(target=self.run_monitor_loop)
        self.monitor_thread.daemon = True # Allows the program to exit cleanly
        self.monitor_thread.start()

    def create_desktop_launcher(self):
        """Creates or updates the custom .desktop launcher for the trash."""
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=My Trash Can
Comment=Contains deleted files, monitored by custom script
Exec=xdg-open trash:///
Icon={ICON_EMPTY_PATH}
Terminal=false
StartupNotify=true
# Custom marker to identify this file as managed by our script
X-Trash-Monitor-Managed=true
"""
        try:
            with open(CUSTOM_DESKTOP_TRASH_FILE, 'w') as f:
                f.write(desktop_content)
            # Make the .desktop file executable
            os.chmod(CUSTOM_DESKTOP_TRASH_FILE, 0o755)
            print(f"Created/updated desktop launcher: {CUSTOM_DESKTOP_TRASH_FILE}")
        except IOError as e:
            print(f"Error creating desktop launcher file: {e}")

    def update_desktop_icon_path_in_file(self, icon_path):
        """Updates the 'Icon=' line in the .desktop file."""
        try:
            with open(CUSTOM_DESKTOP_TRASH_FILE, 'r') as f:
                lines = f.readlines()

            updated_lines = []
            icon_changed = False
            for line in lines:
                if line.startswith("Icon="):
                    if line.strip() != f"Icon={icon_path}": # Only update if different
                        updated_lines.append(f"Icon={icon_path}\n")
                        icon_changed = True
                    else:
                        updated_lines.append(line) # No change needed
                else:
                    updated_lines.append(line)

            if icon_changed:
                with open(CUSTOM_DESKTOP_TRASH_FILE, 'w') as f:
                    f.writelines(updated_lines)
                print(f"Desktop icon path updated to: {icon_path}")
                # Desktop environments usually pick up .desktop file changes automatically.
                # No specific refresh command is typically needed here.
            else:
                print(f"Desktop icon path already set to: {icon_path}")

        except FileNotFoundError:
            print(f"Error: Desktop launcher file not found at {CUSTOM_DESKTOP_TRASH_FILE}. Recreating.")
            self.create_desktop_launcher()
            self.update_desktop_icon_path_in_file(icon_path) # Retry after creation
        except Exception as e:
            print(f"Error updating desktop launcher icon: {e}")

    def is_trash_empty(self):
        """Checks if the trash directory is truly empty."""
        if not os.path.exists(TRASH_DIR_FILES):
            return True
        if not os.listdir(TRASH_DIR_FILES):
            return True
        return False

    def get_last_empty_timestamp(self):
        """Reads the last emptied timestamp from the log file."""
        try:
            with open(LAST_EMPTY_TIMESTAMP_FILE, 'r') as f:
                timestamp_str = f.readline().strip()
                if timestamp_str:
                    return datetime.datetime.fromtimestamp(float(timestamp_str))
                else:
                    return datetime.datetime.now()
        except (FileNotFoundError, ValueError):
            return datetime.datetime.now()

    def set_last_empty_timestamp(self):
        """Writes the current timestamp to the log file, overwriting previous content."""
        try:
            os.makedirs(os.path.dirname(LAST_EMPTY_TIMESTAMP_FILE), exist_ok=True)
            with open(LAST_EMPTY_TIMESTAMP_FILE, 'w') as f:
                f.write(str(datetime.datetime.now().timestamp()))
        except IOError as e:
            print(f"Error writing timestamp file: {e}")

    def update_desktop_icon(self):
        """
        Checks trash status and age, and updates the desktop icon accordingly.
        """
        current_time = datetime.datetime.now()
        trash_is_empty = self.is_trash_empty()

        last_empty_dt = self.get_last_empty_timestamp()
        time_since_empty = current_time - last_empty_dt
        days_since_empty = time_since_empty.days

        icon_to_set = ICON_EMPTY_PATH # Default icon

        if trash_is_empty:
            icon_to_set = ICON_EMPTY_PATH
            # Only update the timestamp file if the recorded time is significantly old
            # This prevents constant file writes if the script is always running
            if (current_time - last_empty_dt).total_seconds() > (CHECK_INTERVAL_SECONDS * 2):
                self.set_last_empty_timestamp()
        else: # Trash is NOT empty
            if days_since_empty >= DAYS_UNTIL_FLIES:
                if os.path.exists(ICON_FLIES_PATH):
                    icon_to_set = ICON_FLIES_PATH
                else:
                    print(f"Warning: Custom flies icon not found at {ICON_FLIES_PATH}. Using empty icon as fallback.")
                    icon_to_set = ICON_EMPTY_PATH # Fallback to empty icon if flies icon is missing
            else:
                icon_to_set = ICON_EMPTY_PATH # Icon remains empty until flies threshold

        # Update the icon in the .desktop file
        self.update_desktop_icon_path_in_file(icon_to_set)

    def run_monitor_loop(self):
        """
        This runs in a separate thread to continuously check the trash status.
        """
        while True:
            self.update_desktop_icon()
            time.sleep(CHECK_INTERVAL_SECONDS)

# Main execution block
if __name__ == "__main__":
    print("Starting desktop trash monitor...")
    monitor = TrashMonitor()
    # The script will now run in the background due to the threading.
    # No Gtk.main() is needed as there's no UI loop.
    # The script will keep running until manually stopped or system shutdown.
    # You might want to add a more robust way to gracefully stop the thread
    # if this were a larger application, but for a simple background monitor,
    # letting it run as a daemon thread is generally fine.
    try:
        # Keep the main thread alive so the daemon thread can run
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Desktop trash monitor stopped by user.")