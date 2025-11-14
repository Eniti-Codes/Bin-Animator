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

# --- Configuration ---
SERVICE_NAME="bin-animator"
APP_DIR="$HOME/.local/share/${SERVICE_NAME}"
SERVICE_FILE="$HOME/.config/systemd/user/${SERVICE_NAME}.service"
SYSTEM_DEPENDENCIES="python3"

# Source directory is the directory where THIS script is located
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
CONFIG_SOURCE_PATH="${SCRIPT_DIR}/config.json"
ANIMATOR_SOURCE_PATH="${SCRIPT_DIR}/Bin-Animator.py"

# --- Functions to clean up installation components ---
cleanup_existing_installation() {
    echo "Stopping existing ${SERVICE_NAME} user service..."
    systemctl --user stop "${SERVICE_NAME}.service" 2>/dev/null
    echo "Disabling existing ${SERVICE_NAME} user service..."
    systemctl --user disable "${SERVICE_NAME}.service" 2>/dev/null

    # Remove files from both possible old locations
    if [ -d "$APP_DIR" ]; then
        echo "Removing old application files from $APP_DIR..."
        rm -rf "$APP_DIR"
    fi
    if [ -d "/opt/${SERVICE_NAME}" ]; then
        echo "Removing old application files from /opt/${SERVICE_NAME} (Requires sudo)..."
        sudo rm -rf "/opt/${SERVICE_NAME}" 2>/dev/null
    fi

    if [ -f "$SERVICE_FILE" ]; then
        echo "Removing old user service file: $SERVICE_FILE"
        rm "$SERVICE_FILE"
    fi
    
    systemctl --user daemon-reload 2>/dev/null
    echo "Existing installation components cleaned up."
}

# --- New function to check for bundled files ---
check_bundled_files() {
    echo "Checking for 'config.json' and 'Bin-Animator.py' in the script directory: $SCRIPT_DIR"
    
    if [ ! -f "$CONFIG_SOURCE_PATH" ]; then
        echo "--- ERROR: Cannot find config.json! ---"
        echo "Expected location: $CONFIG_SOURCE_PATH"
        return 1
    fi
    
    if [ ! -f "$ANIMATOR_SOURCE_PATH" ]; then
        echo "--- ERROR: Cannot find Bin-Animator.py! ---"
        echo "Expected location: $ANIMATOR_SOURCE_PATH"
        return 1
    fi

    echo "Both bundled files found successfully."
    return 0
}

# --- Function to install dependencies ---
install_dependencies() {
    echo "Checking for system dependencies: ${SYSTEM_DEPENDENCIES}..."
    for dep in $SYSTEM_DEPENDENCIES; do
        if ! command -v "$dep" &> /dev/null; then
            echo "Dependency '$dep' not found. Installing now (requires your sudo password)..."
            # We only use sudo for apt-get install
            sudo apt-get update && sudo apt-get install -y "$dep" || { echo "ERROR: Failed to install '$dep'. Aborting."; exit 1; }
        fi
    done
    echo "System dependencies installed."
}

# --- Function to perform core installation/update steps ---
perform_installation_steps() {
    echo "Creating application directory: $APP_DIR"
    mkdir -p "$APP_DIR"

    echo "Copying config.json to $APP_DIR/"
    cp "$CONFIG_SOURCE_PATH" "$APP_DIR/"
    
    echo "Copying Bin-Animator.py to $APP_DIR/"
    cp "$ANIMATOR_SOURCE_PATH" "$APP_DIR/"

    echo "Making Bin-Animator.py executable"
    chmod +x "$APP_DIR/Bin-Animator.py"

    echo "Creating systemd user service file: $SERVICE_FILE"
    mkdir -p "$(dirname "$SERVICE_FILE")"

    cat > "$SERVICE_FILE" <<EOL
[Unit]
Description=Bin Animator Service
After=network.target graphical-session.target
Wants=dbus.service

[Service]
Environment="DISPLAY=:0"
Environment="XDG_RUNTIMR_DIR=/run/user/%U"
ExecStart=/usr/bin/python3 $APP_DIR/Bin-Animator.py --daemon
WorkingDirectory=$APP_DIR
StandardOutput=inherit
StandardError=inherit
Restart=always
RestartSec=5
StartLimitInterval=60
StartLimitBurst=3
Type=simple

[Install]
WantedBy=graphical-session.target
EOL

    echo "Reloading systemd user daemon to recognize changes..."
    systemctl --user daemon-reload

    echo "Enabling ${SERVICE_NAME}.service to start on boot..."
    systemctl --user enable "${SERVICE_NAME}.service"

    echo "Starting ${SERVICE_NAME}.service now..."
    systemctl --user start "${SERVICE_NAME}.service"
}

# --- Main Script Logic ---
if [ "$EUID" -eq 0 ]; then
    echo "ERROR: Please run this script as a normal user, not with sudo."
    echo "The script will ask for your sudo password when needed."
    exit 1
fi

echo "--- Bin Animator Setup & Management ---"
echo "Please choose an option:"
echo "1) Install / Update Bin Animator"
echo "2) Uninstall Bin Animator"
read -rp "Enter your choice (1 or 2): " main_choice

case $main_choice in
    1)
        echo "You chose: Install / Update Bin Animator."
        echo "Proceeding with installation/update..."
        
        # Check for bundled files
        if ! check_bundled_files; then
            exit 1
        fi

        install_dependencies
        cleanup_existing_installation
        perform_installation_steps
        
        echo "--- Installation/Update Complete! ---"
        echo "The Bin Animator service should now be running."
        echo "You can check its status with: systemctl --user status ${SERVICE_NAME}.service"
        echo "You can view its logs with: journalctl --user -u ${SERVICE_NAME}.service"
        ;;

    2)
        echo "You chose: Uninstall Bin Animator."
        echo "Proceeding with uninstallation..."
        
        cleanup_existing_installation
        echo "--- Uninstallation Complete! ---"
        echo "Bin Animator has been successfully removed from your system."
        ;;

    *)
        echo "Invalid choice. Please enter 1 or 2."
        exit 1
        ;;
esac

exit 0
