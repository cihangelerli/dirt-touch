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

stty sane 2>/dev/null
setterm -cursor on 2>/dev/null
tput cnorm 2>/dev/null

python3 -c "import pty; pty.spawn(['/bin/bash', '-i', '-c', 'sudo apt update && sudo apt upgrade -y; echo; read -p \"Press ENTER to return...\"'])"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ] || [ $EXIT_CODE -eq 130 ] || [ $EXIT_CODE -eq 143 ]; then
    exit 0
fi

exit $EXIT_CODE