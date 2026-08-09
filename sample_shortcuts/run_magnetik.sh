#!/bin/bash

# DIRT_TITLE=MAGNETIK
# DIRT_ORDER=2

# Ensure KMSDRM and input drivers are inherited by badhabits.py
export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-kmsdrm}"
export SDL_MOUSEDRV="${SDL_MOUSEDRV:-evdev}"

# Save current terminal settings
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

# Jump to the project directory so relative image paths ('imgs/', 'banners/') still work
cd "$HOME/gen-art-engine" || exit 1

# Run using absolute paths
"$HOME/gen-art-engine/venv/bin/python3" "$HOME/gen-art-engine/display_runner.py" "magnetik"
