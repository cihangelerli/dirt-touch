#!/bin/bash

# Use xterm-256color for proper ncurses border rendering
export TERM=xterm-256color
export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-kmsdrm}"
export SDL_MOUSEDRV="${SDL_MOUSEDRV:-evdev}"

# Rebind fbcon and attach BOTH stdin and stdout to tty1
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

# Spawn nmtui inside a PTY session to provide a valid controlling terminal
python3 -c "import pty; pty.spawn(['sudo', 'nmtui'])"
