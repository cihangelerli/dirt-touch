# main.py
from utils.logger import setup_logger
from launcher import Launcher

def main():
    setup_logger()
    app = Launcher()
    app.run()

if __name__ == "__main__":
    main()