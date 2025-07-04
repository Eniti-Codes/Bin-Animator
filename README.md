# Bin-Animator (for Linux)

Welcome to the **Bin Animator for Linux** project\! This is an open-source initiative to bring an animated trashcan icon to Linux, specifically designed to visually remind you to empty your bin based on how long items have been sitting there.

-----

### The Inspiration

This project was directly inspired by the macOS app **"Banana Bin"**, which I became aware of through a **UFD Tech** YouTube Short. That video showcased an app that animates the trashcan icon, and I loved the idea\! I felt that animating based on how *long* items have been left in the bin would be even more effective and unique – truly capturing that "forgotten trash" feeling.

-----

### My Journey & Project Status

As a developer, this is my **first ever Operating System-level project**, so it's a significant learning experience for me. I'm actively working on it, focusing on getting it stable and functional for Linux Mint users.

**Currently, the project is under active development.** I'm tackling the intricacies of OS integration and desktop environment interaction. While I'm pushing hard to get it working perfectly, I'm committed to the spirit of open-source. This means even if I hit a wall and can't get it fully polished, I'll release the code so others can pick it up, learn from it, and hopefully contribute to its completion.

---

## How it Works

This application monitors your trash folder and changes the system's trash can icon based on its state.

* When your trash is **empty**, a `trash-empty.png` icon is displayed.
* When your trash has **items in it**, a `trash-flies.png` icon is displayed, making it look like flies are buzzing around your full trash!
* If you haven't emptied your trash for a week, the trashcan icon will automatically update to display the `trash-flies.png` icon.

## Requirements

* **Python 3**: You'll need Python 3 installed on your system to run this application.
* **Custom Icons**: For the animation to work, you'll need two PNG image files in your Pictures folder:
    * `trash-empty.png`
    * `trash-full.png`
    * `trash-flies.png`

    Make sure these files are located in your `~/Pictures/` directory (e.g., `/home/yourusername/Pictures/`).

## Installation and Usage

1.  **Clone this repository** (or download the source code).
2.  **Place your custom icons** (`trash-empty.png` and `trash-flies.png`) into your `~/Pictures/` folder.
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

### Contributions Welcome\!

Since I'm new to OS-level development, contributions are absolutely welcome\! If you have experience with Linux system programming, desktop environments, or specifically Linux Mint, your insights would be invaluable. Feel free to explore the code, open issues, or even submit pull requests.

**Disclaimer:** The clarity and structure of this description were assisted by an AI.
