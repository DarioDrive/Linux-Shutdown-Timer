# Linux Shutdown Timer

A lightweight desktop application for Linux that allows you to schedule system shutdown, restart, suspend, or hibernate operations using a simple graphical interface.

Built with Python and Tkinter, Linux Shutdown Timer provides a countdown timer, a progress bar, warning notifications, sound alerts, and system tray integration.

## Features

- **Countdown Timer:** Set the desired time using hours and minutes.
- **Multiple System Actions:** Choose between shutdown, reboot, suspend, or hibernate.
- **Progress Bar:** Visual representation of the remaining time.
- **Final Warning:** Displays a warning window 30 seconds before the scheduled action.
- **Sound Alert:** Plays an alert sound before the action is executed.
- **Cancel Option:** Stop the countdown at any time using the Stop button or the warning window's Cancel button.
- **System Tray Integration:** Minimize the application to the system tray and restore it when needed.
- **Configuration Persistence:** Automatically saves the last used timer settings and selected action.
- **Lightweight Interface:** Simple graphical interface built with Tkinter.

## Requirements

- Linux operating system
- Python 3
- Tkinter
- Pygame
- Pystray
- Pillow
- systemd

## Dependencies

Install the required packages on Debian or Ubuntu-based distributions:

```bash
sudo apt update
sudo apt install python3 python3-tk python3-pip
pip3 install pygame pystray pillow
```

Depending on your distribution, you may need to use a virtual environment to install the Python dependencies.

## Installation

Clone the repository:

```bash
git clone https://github.com/DarioDrive/Linux-Shutdown-Timer.git
```

Enter the project directory:

```bash
cd Linux-Shutdown-Timer
```

Install the Python dependencies if you haven't already.

## Usage

Run the application with:

```bash
python3 linux-shutdown-timer.py
```

1. Set the desired countdown time using the hours and minutes fields.
2. Select the system action:
   - Shutdown
   - Reboot
   - Suspend
   - Hibernate
3. Click **Start Countdown**.
4. The application displays the remaining time and progress.
5. A warning notification appears 30 seconds before the scheduled action.
6. Cancel the countdown if necessary.

The application can also be minimized to the system tray.

## Configuration

The application automatically saves its settings in:

```text
~/.config/apagado-automatico/config.ini
```

The saved settings include the last selected hours, minutes, and system action.

## License

This project is licensed under the **GNU General Public License v2.0 (GPL-2.0)**.

See the [LICENSE](LICENSE) file for details.

## Author

**DarioDrive**

GitHub: [https://github.com/DarioDrive](https://github.com/DarioDrive)
