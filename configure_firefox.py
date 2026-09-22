#!/usr/bin/env python3
from utils import *
import glob
import time
import os
import json
import subprocess

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

# Kill Firefox and wait for it to fully exit (sqlite lock needs to release)
run_command("sudo pkill firefox")
for _ in range(100):  # poll up to ~10s
    if subprocess.run(["pgrep", "firefox"], capture_output=True).returncode != 0:
        break
    time.sleep(0.1)
else:
    run_command("sudo pkill -9 firefox")
    time.sleep(1)

copy_and_overwrite(firefox_settings_file, firefox_settings_path[0]) #note array access for glob

# Set default search engine to DuckDuckGo via enterprise policy
print("-Setting default search engine to DuckDuckGo...")
policies_path = "/usr/lib/firefox/distribution/policies.json"
try:
    with open(policies_path, "r") as f:
        policies = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    policies = {"policies": {}}
policies["policies"]["SearchEngines"] = {"Default": "DuckDuckGo"}
run_command(f"sudo tee {policies_path} > /dev/null << 'EOF'\n{json.dumps(policies, indent=2)}\nEOF")

# Set default zoom to 130%
print("-Setting default zoom to 133%...")
profile_dir = firefox_settings_path[0]
content_prefs_db = f"{profile_dir}/content-prefs.sqlite"
if not os.path.exists(content_prefs_db):
    print("-content-prefs.sqlite not found, launching Firefox briefly to generate it...")
    run_gui_command("firefox")
    time.sleep(3)
    run_command("pkill firefox")
    time.sleep(1)

if os.path.exists(content_prefs_db):
    subprocess.run(["sqlite3", content_prefs_db,
        "INSERT OR IGNORE INTO settings(name) VALUES('browser.content.full-zoom');"
        "INSERT OR REPLACE INTO prefs(groupID, settingID, value) "
        "VALUES(NULL, (SELECT id FROM settings WHERE name = 'browser.content.full-zoom'), '1.33');"
    ], check=True)
    print("-Default zoom set to 133%")
else:
    print("-WARNING: content-prefs.sqlite not found, zoom not set")
    warning_messages.append("Firefox default zoom not set (content-prefs.sqlite missing)")

# Open Firefox to apply user.js settings
run_gui_command("firefox about:preferences")

# Wait 500ms for Firefox to load the user.js file, then delete it
# This ensures user.js is only applied on first launch, but will soft persist in prefs.js
# Which allows for overwriting preferences. (Keeping user.js would reset them on ever start)
time.sleep(0.5)
delete_file(f"{firefox_settings_path[0]}/user.js")
