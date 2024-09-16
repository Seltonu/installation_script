from utils import *

# -------------------------- Configure VSCode --------------------------
# Reads the provided VSCode json file and copies it onto the machine

print("-------------------------- Configuring VSCode")

# Path to the VSCode settings.json file on device
vscode_settings_path = f"{USER_HOME}/.config/Code/User/settings.json"
# Path to backed up settings file
vscode_settings_file = "./configs/vscode/settings.json"

copy_and_overwrite(vscode_settings_file, vscode_settings_path)