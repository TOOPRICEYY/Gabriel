#!/bin/bash

# This script is executed when the countdown reaches zero
# Add your custom commands below

git commit -am "Trapdoor opened"
git push origin main

# Example: Send a notification (uncomment and modify as needed)
# osascript -e 'display notification "Countdown finished!" with title "Timer"'

# Example: Play a sound (uncomment and modify as needed)
# afplay /System/Library/Sounds/Glass.aiff

# Add your custom actions here
