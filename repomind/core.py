import os
import json
import subprocess
from datetime import datetime

REPOMIND_DIR = ".repomind"
CTX = f"{REPOMIND_DIR}/context.md"
DEC = f"{REPOMIND_DIR}/decisions.md"
LOG = f"{REPOMIND_DIR}/session.log"
CFG = f"{REPOMIND_DIR}/config.json"
HIST = f"{REPOMIND_DIR}/history.json"

HISTORY_MAX_TURNS = 20  # rolling window: last N user+assistant pairs

DEFAULT_CHAIN = ["claude_cli", "anthropic_api", "openai", "gemini"]


def ensure():
    os.makedirs(REPOMIND_DIR, exist_ok=True)
    for f in [CTX, DEC, LOG]:
        if not os.path.exists(f):
            open(f, "w").close()
    if not os.path.exists(CFG):
        write_config({"chain": DEFAULT_CHAIN})


def read_config():
    if not os.path.exists(CFG):
        return {"chain": DEFAULT_CHAIN}
    with open(CFG) as f:
        return json.load(f)


def write_config(cfg):
    with open(CFG, "w") as f:
        json.dump(cfg, f, indent=2)


def read_chain() -> list[str]:
    return read_config().get("chain", DEFAULT_CHAIN)


def write_chain(chain: list[str]):
    cfg = read_config()
    cfg["chain"] = chain
    write_config(cfg)


def read_history() -> list[dict]:
    if not os.path.exists(HIST):
        return []
    with open(HIST) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def write_history(history: list[dict]):
    trimmed = history[-(HISTORY_MAX_TURNS * 2):]
    with open(HIST, "w") as f:
        json.dump(trimmed, f, indent=2)


def append_history(role: str, content: str):
    history = read_history()
    history.append({"role": role, "content": content})
    write_history(history)


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
