#!/bin/sh
# softtarget installer for macOS and Linux.
#   curl -fsSL https://raw.githubusercontent.com/ckarandev010/softtarget/main/install.sh | sh
# Installs Ollama if it is missing (official script on Linux, Homebrew on macOS), installs softtarget
# into ~/.softtarget/venv, downloads the model and starts the labs.
# Env overrides: SOFTTARGET_MODEL (model), SOFTTARGET_SRC (pip source, for testing), SOFTTARGET_NO_RUN=1.
set -eu

say() { printf '\033[36m==>\033[0m %s\n' "$1"; }
fail() { printf '\033[31msofttarget install failed:\033[0m %s\n' "$1" >&2; exit 1; }

SRC="${SOFTTARGET_SRC:-https://github.com/ckarandev010/softtarget/archive/refs/heads/main.zip}"
VENV="$HOME/.softtarget/venv"

# 1. Python 3.10+
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
    PY="$c"; break
  fi
done
[ -n "$PY" ] || fail "Python 3.10+ not found. Install it (https://www.python.org/downloads/ or your package manager) and rerun."
say "Using $($PY --version 2>&1)"

# 2. Ollama
if ! command -v ollama >/dev/null 2>&1; then
  case "$(uname -s)" in
    Linux)
      command -v curl >/dev/null 2>&1 || fail "curl is needed to install Ollama"
      say "Installing Ollama with the official script (it may ask for your sudo password)"
      curl -fsSL https://ollama.com/install.sh | sh ;;
    Darwin)
      if command -v brew >/dev/null 2>&1; then
        say "Installing Ollama (Homebrew)"; brew install ollama
      else
        fail "Install Ollama from https://ollama.com/download (or install Homebrew), then rerun."
      fi ;;
    *) fail "Unsupported system $(uname -s). Install Ollama from https://ollama.com/download and run: pip install $SRC" ;;
  esac
fi
command -v ollama >/dev/null 2>&1 || fail "Ollama installed but not on PATH. Open a new terminal and rerun."
say "Ollama found: $(command -v ollama)"

# 3. softtarget in its own virtual environment
if [ ! -x "$VENV/bin/python" ]; then
  say "Creating $VENV"
  mkdir -p "$HOME/.softtarget"
  "$PY" -m venv "$VENV" || fail "could not create a virtual environment. On Debian/Ubuntu: sudo apt install python3-venv"
fi
say "Installing softtarget"
"$VENV/bin/python" -m pip install --quiet --disable-pip-version-check --upgrade "$SRC" || fail "pip install failed"

# 4. Model + first run
if [ -n "${SOFTTARGET_MODEL:-}" ]; then
  "$VENV/bin/python" -m softtarget setup --model "$SOFTTARGET_MODEL" || fail "setup did not finish (see above)"
else
  "$VENV/bin/python" -m softtarget setup || fail "setup did not finish (see above)"
fi

say "Installed. Start it any time with:"
echo "    $VENV/bin/softtarget"
if [ -z "${SOFTTARGET_NO_RUN:-}" ]; then
  if [ -n "${SOFTTARGET_MODEL:-}" ]; then exec "$VENV/bin/softtarget" --model "$SOFTTARGET_MODEL"; else exec "$VENV/bin/softtarget"; fi
fi
