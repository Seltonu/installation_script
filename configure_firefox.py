from utils import *
import glob

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

copy_and_overwrite(firefox_settings_file, firefox_settings_path[0]) #note array access for glob

warn_msg = "Notice: Please note that Firefox default zoom % is not currently automatically configured, \
    this can be changed easily via about:preferences."
print(f"-{warn_msg}")
warning_messages.append(warn_msg)
# run_command("firefox about:preferences")