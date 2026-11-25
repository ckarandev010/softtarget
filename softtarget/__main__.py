import argparse
import sys

from . import __version__, llm, setup_env


def main(argv=None):
    ap = argparse.ArgumentParser(prog="softtarget", description="A deliberately vulnerable LLM app for learning, on your own local model.")
    ap.add_argument("command", nargs="?", choices=["run", "setup"], default="run",
                    help="run (default) starts the labs; setup starts Ollama, downloads the model and tests it")
    ap.add_argument("--model", help=f"Ollama model to use (default {llm.MODEL}, or set SOFTTARGET_MODEL)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--version", action="version", version=f"softtarget {__version__}")
    a = ap.parse_args(argv)
    if a.model:
        llm.MODEL = a.model

    if a.command == "setup":
        return setup_env.run()
    # First run: if the model isn't there yet, set it up before serving.
    if not (setup_env.ollama_up() and setup_env.model_installed(llm.MODEL)):
        if setup_env.run() != 0:
            return 1
    from .server import serve
    serve(a.port, not a.no_browser)
    return 0


if __name__ == "__main__":
    sys.exit(main())
