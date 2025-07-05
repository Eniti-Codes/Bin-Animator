# Bin-Animator (for Linux)

Welcome to the **Bin Animator for Linux** project\! This is an open-source initiative to bring an animated trashcan icon to Linux, specifically designed to visually remind you to empty your bin based on how long items have been sitting there.

-----

### The Inspiration

This project was directly inspired by the macOS app **"Banana Bin"**, which I became aware of through a **UFD Tech** YouTube Short. That video showcased an app that animates the trashcan icon, and I loved the idea\! I felt that animating based on how *long* items have been left in the bin would be even more effective and unique – truly capturing that "forgotten trash" feeling.

-----

## How it Works

This application monitors your trash folder and changes the system's trash can icon based on its state.

* When your trash is **empty**, a `trash-empty.png` icon is displayed.
* When your trash has **items in it**, a `trash-full.png` icon is displayed, To give you a visual reminder that you threw trash away! 
* If you haven't emptied your trash for a week, the trashcan icon will automatically update to display the `trash-flies.png` icon to visually show you that your trash is very old and needs to be taken out.

## Requirements

* **Python 3**: You'll need Python 3 installed on your system to run this application.
* **Custom Icons**: For the animation to work, you'll need two PNG image files in your Pictures folder:
    * `trash-empty.png`
    * `trash-full.png`
    * `trash-flies.png`

    Make sure these files are located in your `~/Pictures/` directory (e.g., `/home/yourusername/Pictures/`).

## Installation and Usage

1.  **Clone this repository** (or download the source code).
2.  **Place your custom icons** (`trash-empty.png` and `trash-full.png` and `trash-flies.png`) into your `~/Pictures/` folder.
3.  **Run the application:** You can launch the application by navigating to the project directory in your terminal and running the main Python script.

    ```bash
    python3 Bin-Animator.py
    ```

## Important Note

---

**Bin Animator is built specifically for Linux Mint.** While it might work on other Linux distributions, its functionality cannot be guaranteed outside of Linux Mint. Compatibility with other distros may vary due to differences in icon theme management and desktop environments.

### Get Daily Updates & Join the Community\!

Want to follow the development of Bin Animator for Linux day-by-day? I post **daily updates** on my progress, challenges, and breakthroughs in my Discord server. This is the best place to get the most current information, offer feedback, or even lend a hand if you're a Linux expert\!

(https://discord.gg/UfyYCRK4jR)

-----

### Current updates\!

Fixed a major bug of the bin animator icon changer not functioning whatsoever.

Fixed the log file not working whatsoever. Now it fully functions.

Added the "stop" command in the command terminal for those that's running it by terminal

Added another requirement for an image file

Overall just cleaned up the code.

-----

### Contributions Welcome\!

Since I'm new to OS-level development, contributions are absolutely welcome\! If you have experience with Linux system programming, desktop environments, or specifically Linux Mint, your insights would be invaluable. Feel free to explore the code, open issues, or even submit pull requests.

**Disclaimer:** The clarity and structure of this description were assisted by an AI.
