#!/bin/bash

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

APP_DIR="/opt/bin-animator"
SERVICE_FILE="/etc/systemd/system/bin-animator.service"
USER_HOME=$(eval echo "~$SUDO_USER")
DOWNLOADS_DIR="$USER_HOME/Downloads"
CONFIG_SOURCE_PATH="$DOWNLOADS_DIR/config.json"
ANIMATOR_SOURCE_PATH="$DOWNLOADS_DIR/Bin-Animator.py"

# --- Function to clean up existing installation components ---
cleanup_existing_installation() {
    echo "Stopping existing Bin Animator service..."
    sudo systemctl stop bin-animator.service 2>/dev/null
    echo "Disabling existing Bin Animator service..."
    sudo systemctl disable bin-animator.service 2>/dev/null

    if [ -d "$APP_DIR" ]; then
        echo "Removing old application files from $APP_DIR..."
        sudo rm -rf "$APP_DIR"
    fi

    if [ -f "$SERVICE_FILE" ]; then
        echo "Removing old systemd service file: $SERVICE_FILE"
        sudo rm "$SERVICE_FILE"
    fi
    sudo systemctl daemon-reload 2>/dev/null
    echo "Existing installation components cleaned up."
}

# --- Function to check for required files in Downloads folder ---
check_download_files() {
    echo "Checking for 'config.json' and 'Bin-Animator.py' in your Downloads folder..."
    if [ ! -f "$CONFIG_SOURCE_PATH" ] || [ ! -f "$ANIMATOR_SOURCE_PATH" ]; then
        echo "--- IMPORTANT: Files Not Found! ---"
        echo "It looks like 'config.json' or 'Bin-Animator.py' are not in your Downloads folder:"
        echo "Expected location for config.json: $CONFIG_SOURCE_PATH"
        echo "Expected location for Bin-Animator.py: $ANIMATOR_SOURCE_PATH"
        echo ""
        echo "Please move both files to your Downloads folder: $DOWNLOADS_DIR"
        echo "Once moved, please run this script again."
        echo ""
        return 1
    fi
    echo "Both files found in Downloads folder."
    return 0
}

# --- Function to perform core installation/update steps ---
# This sequence creates directories, moves files, sets permissions,
# creates the systemd service file, and starts/enables the service.
perform_installation_steps() {
    echo "Creating application directory: $APP_DIR"
    sudo mkdir -p "$APP_DIR"

    echo "Moving config.json to $APP_DIR/config.json"
    sudo mv "$CONFIG_SOURCE_PATH" "$APP_DIR/config.json"
    echo "Moving Bin-Animator.py to $APP_DIR/Bin-Animator.py"
    sudo mv "$ANIMATOR_SOURCE_PATH" "$APP_DIR/Bin-Animator.py"

    echo "Making Bin-Animator.py executable"
    sudo chmod +x "$APP_DIR/Bin-Animator.py"

    echo "Creating systemd service file: $SERVICE_FILE"
    sudo bash -c "cat > \"$SERVICE_FILE\" <<EOL
[Unit]
Description=Bin Animator Service
After=network.target

[Service]
# Ensure common system paths are available for external commands
Environment=\"PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\"
# Execute the Python script, passing --daemon for silent operation
ExecStart=/usr/bin/python3 $APP_DIR/Bin-Animator.py --daemon
# Set the working directory for the script
WorkingDirectory=$APP_DIR
# Direct output to systemd's journal (viewable with journalctl)
StandardOutput=inherit
StandardError=inherit
# Always restart the service if it stops unexpectedly
Restart=always
# Wait 5 seconds before attempting a restart
RestartSec=5
# Limit restart attempts to 3 within a 60-second interval to prevent rapid looping
StartLimitInterval=60
StartLimitBurst=3
# Run the service as the user who executed this script with sudo
User=$SUDO_USER
Group=$SUDO_USER

[Install]
WantedBy=multi-user.target
EOL"

    echo "Reloading systemd daemon to recognize changes..."
    sudo systemctl daemon-reload

    echo "Enabling bin-animator.service to start on boot..."
    sudo systemctl enable bin-animator.service

    echo "Starting bin-animator.service now..."
    sudo systemctl start bin-animator.service
}

# --- Main Menu Presentation and Action Execution ---

echo "--- Bin Animator Setup & Management ---"
echo "Please choose an option:"
echo "1) Install / Update Bin Animator"
echo "2) Uninstall Bin Animator"
read -p "Enter your choice (1 or 2): " choice

case $choice in
    1) # Install / Update Logic
        echo "You chose: Install / Update Bin Animator."
        echo "Proceeding with installation/update..."

        if ! check_download_files; then # Check if files are in Downloads
            exit 1
        fi

        # Always clean up existing components before installing/updating
        # This handles both initial install (cleanup does nothing) and updates
        cleanup_existing_installation

        perform_installation_steps
        echo "--- Installation/Update Complete! ---"
        echo "The Bin Animator service should now be running and will start automatically on future reboots."
        echo "You can check its status with: sudo systemctl status bin-animator.service"
        echo "You can view its logs with: journalctl -u bin-animator.service"
        ;;

    2) # Uninstall Logic
        echo "You chose: Uninstall Bin Animator."
        echo "Proceeding with uninstallation..."
        
        cleanup_existing_installation
        echo "--- Uninstallation Complete! ---"
        echo "Bin Animator has been successfully removed from your system."
        echo "It will no longer start automatically on boot."
        ;;

    *) # Invalid choice
        echo "Invalid choice. Please enter 1 or 2."
        exit 1
        ;;
esac

exit 0
