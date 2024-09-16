# Warning - System Date/Time
If system time is not correct (i.e. when testing in a VM snapshot where the date is in the past), the system's SSL certificate verification will silently fail and cause parts of the scripts to not work such as installing PPAs.

# Gsettings (Gnome)
Running gsettings commands with sudo will silently fail because the exitcode is a false success. The result is "0: command not found".