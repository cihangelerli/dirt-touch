#!/bin/bash

export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-kmsdrm}"
export SDL_MOUSEDRV="${SDL_MOUSEDRV:-evdev}"

STTY_BAK=$(stty -g 2>/dev/null)

cleanup() {
    if [ -n "$STTY_BAK" ]; then
        stty "$STTY_BAK" 2>/dev/null
    fi
    stty echo sane 2>/dev/null
    setterm -cursor on 2>/dev/null
    tput cnorm 2>/dev/null
}

trap cleanup EXIT INT TERM

# Reset console state and show cursor
stty sane 2>/dev/null
setterm -cursor on 2>/dev/null
tput cnorm 2>/dev/null

htop
