import json
import os

BACKUP_DIR = "backups"
BASELINE_FILE = "baseline.json"

def ensure_baseline(items):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    path = os.path.join(BACKUP_DIR, BASELINE_FILE)

    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)

def load_baseline():
    path = os.path.join(BACKUP_DIR, BASELINE_FILE)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)
