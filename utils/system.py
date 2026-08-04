# utils/system.py
import os
import subprocess

def execute_restart():
    """Triggers system reboot."""
    subprocess.Popen(["sudo", "reboot"])

def execute_shutdown():
    """Triggers system shutdown."""
    subprocess.Popen(["sudo", "shutdown", "-h", "now"])