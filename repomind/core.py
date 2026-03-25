import os
import subprocess
from datetime import datetime

REPOMIND_DIR = ".repomind"
CTX = f"{REPOMIND_DIR}/context.md"
DEC = f"{REPOMIND_DIR}/decisions.md"
LOG = f"{REPOMIND_DIR}/session.log"


def ensure():
    os.makedirs(REPOMIND_DIR, exist_ok=True)
    for f in [CTX, DEC, LOG]:
        if not os.path.exists(f):
            open(f, "w").close()


def read(path):
    with open(path, "r") as f:
        return f.read()


def write(path, content):
    with open(path, "w") as f:
        f.write(content)


def append(path, content):
    with open(path, "a") as f:
        f.write(content)


def log(role, text):
    append(LOG, f"\n[{datetime.now()}] {role}:\n{text}\n")


def git_diff():
    try:
        return subprocess.check_output(["git", "diff"], text=True)
    except Exception:
        return ""