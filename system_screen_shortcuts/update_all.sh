#!/bin/bash

export TERM=linux
export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-kmsdrm}"
export SDL_MOUSEDRV="${SDL_MOUSEDRV:-evdev}"

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

echo "========================================="
echo "       STARTING SYSTEM UPDATE           "
echo "========================================="
echo

sudo apt update && sudo apt upgrade -y

echo
echo "========================================="
echo "   UPDATE COMPLETE. RETURNING IN 3S...  "
echo "========================================="
sleep 3
exit 0