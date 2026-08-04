# utils/discovery.py
import os
import glob
from typing import List, Dict, Any

def discover_applications() -> List[Dict[str, Any]]:
    """Scans $HOME for run_*.sh wrapper scripts and parses metadata tags."""
    home_dir = os.path.expanduser("~")
    pattern = os.path.join(home_dir, "run_*.sh")
    script_paths = glob.glob(pattern)
    
    apps = []
    
    for path in script_paths:
        filename = os.path.basename(path)
        # Default title derived from filename: run_badhabits.sh -> BAD HABITS
        raw_name = filename[4:-3] if filename.startswith("run_") and filename.endswith(".sh") else filename
        default_title = raw_name.replace("_", " ").upper()
        
        metadata = {
            "path": path,
            "filename": filename,
            "title": default_title,
            "category": "APP",
            "order": 999,
            "color": "APP"
        }
        
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("# DIRT_TITLE="):
                        metadata["title"] = line.split("=", 1)[1].replace("\\n", "\n").upper()
                    elif line.startswith("# DIRT_CATEGORY="):
                        metadata["category"] = line.split("=", 1)[1].strip()
                    elif line.startswith("# DIRT_ORDER="):
                        try:
                            metadata["order"] = int(line.split("=", 1)[1].strip())
                        except ValueError:
                            pass
                    elif line.startswith("# DIRT_COLOR="):
                        metadata["color"] = line.split("=", 1)[1].strip()
        except Exception as e:
            pass
            
        apps.append(metadata)
        
    # Sort primary by DIRT_ORDER, secondary by title
    apps.sort(key=lambda a: (a["order"], a["title"]))
    return apps