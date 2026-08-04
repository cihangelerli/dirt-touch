# utils/process.py
import os
import sys
import subprocess
import pygame
from typing import Tuple, Optional
from utils.logger import log_info, log_error

def run_application(script_path: str) -> Tuple[bool, str, int]:
    """Executes child app script and returns status, stderr/message, exit_code."""
    log_info(f"Launching application wrapper: {script_path}")
    
    if not os.path.exists(script_path):
        return False, "File Not Found", 404
        
    if not os.access(script_path, os.X_OK):
        return False, "Permission Denied (EACCES)", 126

    try:
        # Pause Pygame rendering state
        pygame.display.iconify()
        
        proc = subprocess.Popen([script_path], stdout=None, stderr=subprocess.PIPE)
        _, stderr = proc.communicate()
        exit_code = proc.returncode
        
        if exit_code != 0:
            err_msg = stderr.decode("utf-8", errors="ignore").strip() if stderr else f"Exit code {exit_code}"
            log_error(f"App {script_path} failed with code {exit_code}: {err_msg}")
            return False, err_msg, exit_code
            
        return True, "Success", 0
    except Exception as e:
        log_error(f"Execution error for {script_path}: {str(e)}")
        return False, str(e), 1
    finally:
        # Guarantee display context remains active
        if not pygame.display.get_init():
            pygame.display.init()

def run_terminal_session(launcher=None):
    """Launches interactive bash shell session with full display re-initialization."""
    log_info("Executing interactive Terminal session")
    try:
        pygame.display.quit()
        os.system("clear")
        os.system("bash")
        os.system("stty sane")
        os.system("clear")
    finally:
        if launcher:
            launcher.reinit_display()
        else:
            pygame.display.init()
            pygame.display.set_mode((640, 480))