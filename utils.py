import subprocess
import os
import shutil
"""
    File for global utility functions and global vars
"""

USER_HOME = os.path.expanduser("~")
error_messages = []
warning_messages = []

# -------------------------- Run Functions --------------------------

# used for calling a bash command and printing/returning outputs 
def run_command(command, print_stdout=True):
    global error_messages
    
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # read out stdout line by line in real time
    while True and print_stdout:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
    # collect stderr at end
    stderr = process.communicate()[1]
    
    if process.returncode != 0 and stderr:
        error_messages.append(str(stderr))
    
    result = {
        "returncode": process.returncode,
        "stdout": process.communicate()[0],
        "stderr": process.communicate()[1]
    }
    return result

def run_script(script_path, args=""):
    command = f"./{script_path} {args}"
    result = run_command(command)
    return result

# -------------------------- File Functions --------------------------

def copy_and_overwrite(local_file, device_path) -> bool:
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(device_path), exist_ok=True)
        shutil.copy(local_file, device_path)
    except FileNotFoundError:
        err_msg = f"Settings file not found at {local_file}"
        error_messages.append(err_msg)
        print("Error: " + err_msg)
        return False
    except Exception as e:
        err_msg = f"Failed to copy {local_file} to {device_path}. Error: {e}"
        error_messages.append(err_msg)
        print("Error: " + err_msg)
        return False
    print("-Settings succesfully copied")
    return True


# -------------------------- Misc. Functions --------------------------

def is_gnome_session() -> bool:
    if ("GNOME" in run_command("echo $XDG_CURRENT_DESKTOP", False)["stdout"].upper()):
        return True
    else:
        return False

def is_package_installed(package_name) -> bool:
    returncode = run_command(f"dpkg -l | grep -qw {package_name}")["returncode"]
    if (returncode == 0):
        return True
    else:
        return False