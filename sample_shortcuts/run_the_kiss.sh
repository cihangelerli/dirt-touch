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

clear

setterm -cursor off 2>/dev/null

/usr/bin/mpv \
    --no-audio \
    --vo=gpu \
    --gpu-context=drm \
    --loop-file=inf \
    --input-terminal=yes \
    --input-vo-keyboard=yes \
    "$HOME/video/the_kiss.mp4"

EXIT_CODE=$?

# Convert mpv signal shutdown (code 4, 130, 143) into clean exit status 0
if [ $EXIT_CODE -eq 4 ] || [ $EXIT_CODE -eq 130 ] || [ $EXIT_CODE -eq 143 ]; then
    exit 0
fi

exit $EXIT_CODE
