#!/bin/bash
# DIRT_TITLE=TERMINAL
# DIRT_ORDER=5

export TERM=linux
export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-kmsdrm}"
export SDL_MOUSEDRV="${SDL_MOUSEDRV:-evdev}"

# Rebind fbcon and attach stdin/stdout to tty1
echo 1 | sudo tee /sys/class/vtconsole/vtcon1/bind >/dev/null 2>&1
sudo chvt 1 2>/dev/null
sudo kbd_mode -a -C /dev/tty1 2>/dev/null

exec < /dev/tty1 > /dev/tty1 2>&1

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

stty sane 2>/dev/null
setterm -cursor on 2>/dev/null
tput cnorm 2>/dev/null

clear

/bin/bash --login
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ] || [ $EXIT_CODE -eq 130 ] || [ $EXIT_CODE -eq 143 ]; then
    exit 0
fi

exit $EXIT_CODE
