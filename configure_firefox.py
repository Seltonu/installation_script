from utils import *
import glob
import time
import os

# -------------------------- Configure Firefox --------------------------
# Overwrites the Firefox user_prefs file with the local copy.
# NOTE: Firefox MUST be launched at least once prior to starting this script,
# so that the default-release directory will be generated

print("-------------------------- Configuring Firefox")

firefox_settings_path = glob.glob(f"{USER_HOME}/.mozilla/firefox/*.default-release")
firefox_settings_file = "./configs/firefox/user.js"

if (not firefox_settings_path):
    err_msg = "Firefox default-release not found. Please launch Firefox once, and rerun configure_firefox.py"
    print(f"-ERROR: {err_msg}")
    error_messages.append(err_msg)
    exit(1)

run_command("sudo pkill firefox"); # Necessary for user.js to be applied

copy_and_overwrite(firefox_settings_file, firefox_settings_path[0]) #note array access for glob

# Open Firefox to set default zoom and search engine
print("-Opening Firefox preferences...")
print(" Please manually set:")
print("   1. Default zoom to 133% (scroll down to 'Zoom' section)")
print("   2. Default search engine to DuckDuckGo (in the 'Search' tab)")
run_gui_command("firefox about:preferences")

# Wait 500ms for Firefox to load the user.js file, then delete it
# This ensures user.js is only applied on first launch, but will soft persist in prefs.js
# Which allows for overwriting preferences. (Keeping user.js would reset them on ever start)
time.sleep(0.5)
delete_file(f"{firefox_settings_path[0]}/user.js")

warn_msg = "Manual Firefox configuration required: Set default zoom to 133% and search engine to DuckDuckGo"
warning_messages.append(warn_msg)
