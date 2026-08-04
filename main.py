# main.py
import os

# Set SDL2 environment variables BEFORE initializing pygame
os.environ.setdefault("SDL_VIDEODRIVER", "kmsdrm")
os.environ.setdefault("SDL_MOUSEDRV", "evdev")

# Flexible touch device resolution:
# 1. Respect explicit SDL_TOUCH_DEVICE if already present in environment/systemd
# 2. Check for optional TOUCH_DEVICE environment variable override
# 3. Check for stable persistent symlink (/dev/input/touchscreen)
# 4. Fall back to letting SDL2/evdev auto-discover devices across /dev/input/event*
if "SDL_TOUCH_DEVICE" not in os.environ:
    if "TOUCH_DEVICE" in os.environ:
        os.environ["SDL_TOUCH_DEVICE"] = os.environ["TOUCH_DEVICE"]
    elif os.path.exists("/dev/input/touchscreen"):
        os.environ["SDL_TOUCH_DEVICE"] = "/dev/input/touchscreen"

from utils.logger import setup_logger
from launcher import Launcher

def main():
    setup_logger()
    app = Launcher()
    app.run()

if __name__ == "__main__":
    main()