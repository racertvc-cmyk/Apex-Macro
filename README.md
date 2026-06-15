Apex Macro 🎯

A lightweight, modern, dark-themed macro recorder built in Python. Apex Macro allows you to record your keyboard keystrokes and mouse movements/clicks, and replay them with advanced customization like speed adjustment, loop counts, loop delays, and humanized timing.

This project is 100% open-source and transparent so you can audit the code, run it directly from the source, or build the executable yourself.

✨ Features

Global Recording & Replay: Easily record macros using F8 and replay them using F12. Stop instantly with F6.

Auto-Minimize on Play: The window automatically minimizes during replay to keep focus on your target window (like Roblox or other applications) and restores itself when finished.

Input Filtering: Choose whether to record mouse clicks, mouse movements, or keyboard keystrokes individually.

Timing Customization: Adjust playback speed ($0.5\times$ to $10\times$), set a delay between loops, or add a Humanize Delay to randomize wait times slightly for natural gameplay.

Clean Dark Theme: Modern borderless UI with neon accents.

🛡️ Transparency & Safety (No Malware)

Pre-compiled .exe files created with PyInstaller can sometimes trigger false positive alerts from antivirus programs (such as Windows Defender). This is a well-known issue because PyInstaller packs the Python interpreter and the script into a single compressed binary.

To ensure your safety, you do not have to run any pre-built .exe files! You can run this macro directly from the Python source code by following the steps below.

🚀 How to Run from Source (Recommended)

To run Apex Macro without using a pre-compiled executable, you can run the raw Python code directly:

Prerequisite: Install Python

Ensure you have Python 3.8 or newer installed on your computer. You can download it from the official website: python.org.

Step 1: Clone the Repository

Clone this repository or download the tinytask_dark.py file to your computer.

Step 2: Install Dependencies

Open your Command Prompt (cmd) or Terminal, navigate to the folder where the file is located, and install the required pynput library:

pip install pynput


(Note: If you run the script without installing it, the built-in loader will attempt to install it for you automatically!)

Step 3: Run the Script

Start the macro by running:

python tinytask_dark.py


🛠️ How to Compile to .exe Yourself

If you prefer using an .exe but want to be absolutely sure of its safety, you can compile the code yourself using your own machine:

Install PyInstaller:

pip install pyinstaller


Build the single-file executable:

pyinstaller --onefile --noconsole tinytask_dark.py


Once completed, your custom-built executable will be waiting safely inside the newly created dist folder!

📜 License

This project is licensed under the MIT License - feel free to use, modify, and distribute it!
