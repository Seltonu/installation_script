#!/bin/bash

echo "-------------------------- VSCode Configuration --------------------------"

# Path to the VSCode settings.json file
vscode_settings_file="$HOME/.config/Code/User/settings.json"
settings_json="./configs/vscode/settings.json"

# Check if the VSCode settings.json file exists
if [ ! -f "$vscode_settings_file" ]; then
    # Create the directory and file if they don't exist
    mkdir -p "$HOME/.config/Code/User"
    touch "$vscode_settings_file"
fi

# Check if the settings.json file exists
if [ -f "$settings_json" ]; then
    # Replace the contents of the VSCode settings.json file with the contents of settings_json
    cp "$settings_json" "$vscode_settings_file"
    printf "VSCode configuration complete.\n"
else
    printf "Error: VSCode settings file not found at $settings_json\n"
fi
