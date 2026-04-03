#!/bin/bash
#!/usr/bin/python3

error_messages=""

./configure_flameshot.sh && echo "Flameshot configuration succesful." || error_messages+="ERROR: Flameshot configuration failed.\n"

if [ -n "$error_messages" ]; then
    printf "Errors occurred:\n$error_messages"
else
    printf "No errors.\n"
fi