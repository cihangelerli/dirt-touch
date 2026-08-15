#!/bin/bash

# DIRT_TITLE=GLITCHBOOTH SLIDESHOW
# DIRT_ORDER=4

# Check if cog is installed
if ! command -v cog &> /dev/null; then
    echo "Error: 'cog' browser launcher is not installed or not in PATH." >&2
    exit 1
fi

# Ensure KMSDRM and input drivers are inherited
export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-kmsdrm}"
export SDL_MOUSEDRV="${SDL_MOUSEDRV:-evdev}"

# Save current terminal settings if in a valid TTY
STTY_BAK=$(stty -g 2>/dev/null)

# Trap signals in the wrapper script to ensure cleanup on exit
cleanup() {
    # Restore terminal settings
    if [ -n "$STTY_BAK" ]; then
        stty "$STTY_BAK" 2>/dev/null
    fi
    # Force reset tty state and restore cursor visibility
    stty echo sane 2>/dev/null
    setterm -cursor on 2>/dev/null
    tput cnorm 2>/dev/null
}

trap cleanup EXIT INT TERM

clear

# Run cog to display glitchbooth slideshow
cog https://glitchbooth.online/slideshow
EXIT_CODE=$?

# If cog exited via SIGSEGV (139) or SIGINT/SIGTERM (130/143), treat as clean exit
if [ $EXIT_CODE -eq 139 ] || [ $EXIT_CODE -eq 130 ] || [ $EXIT_CODE -eq 143 ]; then
    exit 0
fi

exit $EXIT_CODE
