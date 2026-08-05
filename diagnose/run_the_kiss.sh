#!/bin/bash

# DIRT_TITLE=THE KISS
# DIRT_ORDER=3

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

setterm -cursor off 2>/dev/null

# --input-terminal=yes and --input-vo-keyboard=yes enable ESC -> quit on KMSDRM
/usr/bin/mpv \
    --vo=gpu \
    --gpu-context=drm \
    --loop-file=inf \
    --input-terminal=yes \
    --input-vo-keyboard=yes \
    "$HOME/video/the_kiss.mp4"
