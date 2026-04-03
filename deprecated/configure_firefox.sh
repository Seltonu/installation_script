#!/bin/bash

echo "-------------------------- Firefox Configuration --------------------------"

# Directory where the user.js file is located
config_file="./configs/firefox/user.js"

# Directory where the Firefox profile with the random string is located
firefox_profile_dir="$HOME/.mozilla/firefox"

# Find the <random_string>.default-release directory
default_release_dir=$(ls -d "$HOME/.mozilla/firefox"/*.default-release/ 2>/dev/null | head -n 1)

# Check if a profile directory was found
if [ -n "$default_release_dir" ]; then
    # Copy the user.js file to the profile directory
    cp "$config_file" "$default_release_dir/"
    echo "user.js file copied to Firefox profile directory: $default_release_dir"
else
    echo "ERROR: Firefox profile directory not found."
    exit 1
fi

printf "Firefox configuration complete.\n"