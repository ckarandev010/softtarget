"""`softtarget setup`: make sure Ollama is running and the model is downloaded."""
import json
import platform
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

from . import llm

INSTALL_HINT = {
    "Windows": "winget install -e --id Ollama.Ollama   (or download from https://ollama.com/download)",
    "Darwin": "brew install ollama   (or download from https://ollama.com/download)",
    "Linux": "curl -fsSL https://ollama.com/install.sh | sh",
}


def say(msg):
    print(f"==> {msg}", flush=True)


def ollama_up():
    try:
        with urllib.request.urlopen(llm.HOST + "/api/version", timeout=3) as r:
            return json.loads(r.read()).get("version", "?")
    except Exception:  # noqa: BLE001
        return None


def start_ollama(wait=20):
    exe = shutil.which("ollama")
    if not exe:
        return False
    say("Starting Ollama")
    kw = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "stdin": subprocess.DEVNULL}
    if platform.system() == "Windows":
        kw["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True
    subprocess.Popen([exe, "serve"], **kw)
    for _ in range(wait * 2):
        if ollama_up():
            return True
        time.sleep(0.5)
    return False


def model_installed(model):
    h = llm.health()
    return model in h.get("installed", [])


def size(n):
    return f"{n / 1e9:.2f} GB" if n >= 1e9 else f"{n / 1e6:.0f} MB"


def pull(model):
    """Download a model through Ollama's API, with a progress line."""
    req = urllib.request.Request(llm.HOST + "/api/pull", data=json.dumps({"model": model, "stream": True}).encode(),
                                 headers={"Content-Type": "application/json"})
    last = ""
    with urllib.request.urlopen(req, timeout=3600) as r:
        for line in r:
            if not line.strip():
                continue
            ev = json.loads(line)
            if ev.get("error"):
                raise llm.LLMError(ev["error"])
            status, total, done = ev.get("status", ""), ev.get("total"), ev.get("completed")
            if total and done is not None:
                pct = done / total * 100
                bar = "#" * int(pct / 4)
                text = f"\r    {status[:24]:24} [{bar:25}] {pct:5.1f}%  {size(done)}/{size(total)}"
            else:
                text = f"\r    {status[:70]:70}"
            if text != last:
                sys.stdout.write(text)
                sys.stdout.flush()
                last = text
    sys.stdout.write("\n")


def smoke_test():
    reply = llm.chat([{"role": "user", "content": "Reply with the single word: ready"}], temperature=0)
    return reply.get("content", "").strip()


def run(model=None):
    """Return 0 when everything is ready, 1 otherwise."""
    if model:
        llm.MODEL = model
    model = llm.MODEL
    if sys.version_info < (3, 10):
        print("softtarget needs Python 3.10 or newer.")
        return 1
    v = ollama_up()
    if not v and not start_ollama():
        if shutil.which("ollama"):
            print(f"Ollama is installed but not answering at {llm.HOST}. Start it (ollama serve) and rerun.")
        else:
            print("Ollama isn't installed. Install it, then rerun `softtarget setup`:\n    "
                  + INSTALL_HINT.get(platform.system(), "https://ollama.com/download"))
        return 1
    say(f"Ollama {ollama_up()} running at {llm.HOST}")
    if model_installed(model):
        say(f"Model {model} already downloaded")
    else:
        say(f"Downloading {model} (qwen2.5:7b is about 4.7 GB; needs ~8 GB of RAM or VRAM to run well)")
        try:
            pull(model)
        except (urllib.error.URLError, llm.LLMError) as e:
            print(f"Download failed: {e}")
            return 1
    say("Testing the model (the first answer is slow while it loads)")
    try:
        out = smoke_test()
    except llm.LLMError as e:
        print(f"Model test failed: {e}")
        return 1
    say(f"Model answered: {out[:40]!r}")
    say("Ready. Start the labs with: softtarget")
    return 0
