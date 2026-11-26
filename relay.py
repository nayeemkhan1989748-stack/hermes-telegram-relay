"""Poll Telegram, turn a message into a Kaggle Hermes run.

Designed for GitHub Actions (public repo, free). No long-running server.
Secrets come from GitHub Actions repository secrets.
"""
import json
import os
import subprocess
from pathlib import Path

import requests

TG = os.environ["TELEGRAM_BOT_TOKEN"]
KAGGLE_TOKEN = os.environ["KAGGLE_API_TOKEN"]
ALLOWED = int(os.environ.get("TELEGRAM_ALLOWED_USERS", "6729267449"))
SLUG = os.environ.get("KAGGLE_SLUG", "nayeemkhan1231/hermes-agent-kaggle")
API = f"https://api.telegram.org/bot{TG}"
STATE = Path("state.json")
NB = Path("nb")


def tg(method, **data):
    r = requests.post(API + "/" + method, data=data, timeout=60)
    r.raise_for_status()
    return r.json()


def read_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {}


def write_state(state):
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def kaggle(*args):
    env = os.environ.copy()
    env["KAGGLE_API_TOKEN"] = KAGGLE_TOKEN
    subprocess.run(["kaggle", *args], check=True, env=env, timeout=600)


def submit(task: str) -> None:
    NB.mkdir(exist_ok=True)
    kaggle("kernels", "pull", SLUG, "-p", str(NB), "-m")
    notebooks = list(NB.glob("*.ipynb"))
    if not notebooks:
        raise RuntimeError("no notebook pulled")
    path = notebooks[0]
    nb = json.loads(path.read_text())
    patched = False
    for cell in nb["cells"]:
        if cell.get("id") == "cell-5":
            lines = "".join(cell["source"]).splitlines(True)
            for i, line in enumerate(lines):
                if line.startswith("TASK = "):
                    lines[i] = "TASK = " + json.dumps(task, ensure_ascii=False) + "\n"
                    patched = True
            cell["source"] = "".join(lines).splitlines(True)
    if not patched:
        raise RuntimeError("TASK line not found")
    path.write_text(json.dumps(nb, indent=2, ensure_ascii=False))
    kaggle("kernels", "push", "-p", str(NB))


def main() -> None:
    state = read_state()
    updates = tg("getUpdates", offset=state.get("offset", 0), timeout=10).get("result", [])
    if not updates:
        return
    top = max(u["update_id"] for u in updates) + 1
    if "offset" not in state:
        write_state({"offset": top})  # ignore backlog on first run
        return

    tasks = []
    for u in updates:
        msg = u.get("message") or u.get("edited_message") or {}
        if msg.get("from", {}).get("id") != ALLOWED:
            continue
        text = msg.get("text", "").strip()
        if not text or text.startswith("/"):
            continue
        tasks.append(text)

    write_state({"offset": top})
    if not tasks:
        return

    task = tasks[0]
    tg("sendMessage", chat_id=ALLOWED, text="⏳ Queued on Kaggle: " + task[:250])
    submit(task)
    tg("sendMessage", chat_id=ALLOWED,
       text="🚀 Running on Kaggle — final reply/files will arrive here.")


if __name__ == "__main__":
    main()
