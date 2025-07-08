# Bin-Animator (for Linux)

Welcome to the **Bin Animator for Linux** project\! This is an open-source initiative to bring an animated trashcan icon to Linux, specifically designed to visually remind you to empty your bin based on how long items have been sitting there.

-----

### The Inspiration

This project was directly inspired by the macOS app **"Banana Bin"**, which I became aware of through a **UFD Tech** YouTube Short. That video showcased an app that animates the trashcan icon, and I loved the idea\! I felt that animating based on how *long* items have been left in the bin would be even more effective and unique – truly capturing that "forgotten trash" feeling.

-----

## Bin-Animator: Installation & Setup Guide

This guide will walk you through setting up and managing the Bin-Animator application.

-----

### How Bin-Animator Works

Bin-Animator is designed to provide visual feedback on the state of your system's trash folder.

  * When your trash is **empty**, a `trash-empty.png` icon is displayed.
  * When your trash has **items in it**, a `trash-full.png` icon is displayed, serving as a visual reminder that you've discarded items.
  * If your trash hasn't been emptied for a week, the icon will automatically update to display the `trash-flies.png` icon, visually indicating that your trash is old and needs to be taken out.

-----

### Requirements

  * **Python 3**: You'll need Python 3 installed on your system to run this application.
  * **Custom Icons**: For the animation to work, you'll need three PNG image files in your `~/Pictures/` folder:
      * `trash-empty.png`
      * `trash-full.png`
      * `trash-flies.png`
        Make sure these files are located in your `~/Pictures/` directory (e.g., `/home/yourusername/Pictures/`).

-----

### Important Pre-requisites

  * **Bin-Animator Files:** The core Bin-Animator files, specifically `Bin-Animator.py` and `config.json`, **must** be unzipped and located directly in your user's `Downloads` directory (`~/Downloads/`). The setup script won't work if these files are still in a zipped archive or a subfolder.

-----

### Option 1: Install as a System Service (Recommended for Linux Mint Users)

The `Setup-Bin-Animator.sh` script is designed to install Bin-Animator as a system service, allowing it to run automatically in the background without needing to reboot. This setup is specifically configured for Linux Mint.

#### Purpose

This script streamlines the installation by presenting an interactive menu for installation or uninstallation. For installation, it automatically moves Bin-Animator files from your `Downloads` directory to a designated system-wide location, configures the Python script to run automatically as an operating system service (using `systemd`), and starts the service immediately. For uninstallation, it removes these system files and undoes all customizations. The script also provides helpful messages and can update existing Bin-Animator files.

#### Installation & Uninstallation Steps

1.  **Get the Setup Script:**
    First, ensure you have the `Setup-Bin-Animator.sh` script. If you've cloned the repository or downloaded the source code, this script should be with the other Bin-Animator files.

2.  **Navigate to the Script's Location:**
    Open your terminal and go to the directory where you've saved the `Setup-Bin-Animator.sh` script. This is typically your `Downloads` directory.

    ```bash
    cd ~/Downloads/
    ```

3.  **Make the Script Executable:**
    Before you can run the script, you need to give it permission to execute.

    ```bash
    chmod +x Setup-Bin-Animator.sh
    ```

4.  **Run the Setup Script with `sudo`:**
    Execute the script using `sudo`. This is **required** because the script sets up a system-level `systemd` service to allow the Python script to run automatically. While the `Setup-Bin-Animator.sh` script requires `sudo`, the main `Bin-Animator.py` Python script itself does *not* run with `sudo` privileges.

    ```bash
    sudo ./Setup-Bin-Animator.sh
    ```

5.  **Follow the On-Screen Prompts:**
    Once executed, the script will present you with an interactive menu in the terminal:

      * To **install**, type `1` and press `Enter`. The script will automatically move the necessary files, set up the `systemd` service, and start the Bin-Animator service. You don't need to reboot.
      * To **uninstall**, type `2` and press `Enter`. The script will remove the `systemd` configuration, delete the files from the custom directory, and revert any system customizations.

-----

### Option 2: Run Manually (Without System Service)

If you prefer not to install Bin-Animator as a system service or are using an operating system other than Linux Mint, you can run the Python script manually.

1.  **Get Bin-Animator Files:**
    Ensure you have `Bin-Animator.py` and `config.json` in a convenient directory. If you've cloned the repository, navigate to that directory.

2.  **Run the Application:**
    Open your terminal, navigate to the directory where `Bin-Animator.py` is located, and execute the script directly using Python:

    ```bash
    python3 Bin-Animator.py
    ```

      * The application will run as long as the terminal window remains open. To stop it, close the terminal or press `Ctrl+C` in the terminal.

-----

### Important Notes

  * **Linux Mint Specific:** This application and its `Setup-Bin-Animator.sh` script are purposely designed and tested for **Linux Mint**. I cannot guarantee it will function correctly on other Linux distributions or desktop environments, and I won't be able to provide support for issues encountered outside of Linux Mint due to limited access to other systems.
  * **No Manual Python Run Needed (Option 1):** If you've installed Bin-Animator via **Option 1 (System Service)**, you **don't** need to manually run `python3 Bin-Animator.py`. The setup script handles starting the application as a background service.
  * **`config.json` File Warning:** This guide and the `Setup-Bin-Animator.sh` script are designed for the default Bin-Animator file structure. If you modify the `config.json` file *before* running the setup script, the installation or uninstallation might not work as expected. For customized setups after modifying `config.json`, you might need to manually move or remove files.

-----


### Get Daily Updates & Join the Community\!

Want to follow the development of Bin Animator for Linux day-by-day? I post **daily updates** on my progress, challenges, and breakthroughs in my Discord server. This is the best place to get the most current information, offer feedback, or even lend a hand if you're a Linux expert\!

(https://discord.gg/UfyYCRK4jR)

-----

### Current updates\!

Made an entire setup file for those that want it to run in the background on their system. This would include installing and uninstalling it from the background processes.

The README has been fully redesigned. to encourage those to run it as a background process because it's the most efficiently

Fix the prints not working when you run it strictly in terminal. I thought it would be a way more complex issue to fix. I just had to copy and paste some old code that I was messing with and it just functioned. So here's the update.

-----

### Contributions Welcome\!

Since I'm new to OS-level development, contributions are absolutely welcome\! If you have experience with Linux system programming, desktop environments, or specifically Linux Mint, your insights would be invaluable. Feel free to explore the code, open issues, or even submit pull requests.

**Disclaimer:** The clarity and structure of this description were assisted by an AI.
