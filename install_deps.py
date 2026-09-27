import os
import sys
import subprocess

# Determine target directory
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_DIR = os.path.join(CURR_DIR, "suutego", "libraries")

def install_requirements():
    requirements_file = os.path.join(CURR_DIR, "requirements.txt")
    if not os.path.exists(requirements_file):
        print("No requirements.txt found.")
        return

    print(f"Installing dependencies into {TARGET_DIR}...")
    
    # Run pip targeting the local folder
    cmd = [
        sys.executable, "-m", "pip", "install",
        "-r", requirements_file,
        "--target", TARGET_DIR
    ]
    
    subprocess.check_call(cmd)
    print("Done! Dependencies installed successfully.")

if __name__ == "__main__":
    install_requirements()