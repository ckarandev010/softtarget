# softtarget

**A deliberately vulnerable LLM app for learning AI security, running entirely on your own machine.**

Web apps have DVWA. softtarget does the same for LLM apps: small apps built around a local model, each
with four security levels, where you attack the app until it gives up a secret.

The model isn't the vulnerable part. The bugs are in how the app uses it: secrets in the prompt, model
output rendered as HTML, untrusted text mixed into instructions, tools with more access than the user.
Those are the mistakes real LLM features ship with, and they map to the
[OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/llm-top-10/).

Everything runs locally through [Ollama](https://ollama.com). No API keys, no cloud, nothing leaves your
machine.

## Labs

| # | Lab | OWASP LLM | You win when |
|---|---|---|---|
| 1 | Secret in the prompt | LLM07, LLM01 | the support bot reveals a staff code from its instructions |
| 2 | Poisoned ticket | LLM01 (indirect), LLM02 | a ticket you write makes the staff assistant leak an API key outside the company |
| 3 | Rendered output | LLM05 | JavaScript runs in the chat page |
| 4 | Too much access | LLM06 | you read another customer's order through the bot's database tools |

Each lab has four levels:

- **low**: no defence
- **medium**: the defence people usually add first (a blocklist, delimiter tags, read-only SQL...)
- **high**: a stronger defence with a real gap
- **impossible**: the design that actually fixes it, so you can see what "right" looks like

The side panel shows every tool call, every filter that fired and every leak, so you can see why an
attack worked. Secrets are random per session; every player gets a private database.

## Install

One line. It installs Python and [Ollama](https://ollama.com) if they're missing, installs softtarget in its
own virtual environment (`~/.softtarget`), downloads the model (qwen2.5:7b, about 4.7 GB), tests it and opens
the labs.

**Windows (PowerShell)**

```
irm https://raw.githubusercontent.com/ckarandev010/softtarget/main/install.ps1 | iex
```

**macOS / Linux**

```
curl -fsSL https://raw.githubusercontent.com/ckarandev010/softtarget/main/install.sh | sh
```

Read a script before piping it into your shell. Both are short: [install.ps1](install.ps1), [install.sh](install.sh).
On Linux, Ollama's own installer may ask for your sudo password. On macOS without Homebrew, install Ollama
from ollama.com first.

**Already have Ollama and Python?**

```
pip install https://github.com/ckarandev010/softtarget/archive/refs/heads/main.zip
softtarget
```

The first run downloads the model if it isn't there (`softtarget setup` does only that step). The labs open
at `http://127.0.0.1:8765/`.

**Hardware.** qwen2.5:7b needs about 8 GB of free RAM or VRAM. On a GPU replies take a few seconds; CPU-only
works but is much slower. Use another model with `softtarget --model llama3.1:8b` (or `SOFTTARGET_MODEL`),
and another Ollama server with `SOFTTARGET_OLLAMA=http://host:11434`. Labs 2 and 4 need a model that
supports tool calling.

Results depend on the model. Every level below "impossible" has been beaten on qwen2.5:7b-instruct
(Q4, 8 GB GPU). Medium levels usually take a few tries; that's the point.

## Safety

This app is vulnerable on purpose. It binds to 127.0.0.1 only. Don't expose it to a network. The labs
use a fictional company and fake data; the "emails" and "image requests" in lab 2 are recorded, never
sent.

## Develop

```
pip install -e .[dev]
pytest -q
```

The tests drive every level with a scripted fake model, so they run without Ollama.

MIT licence. Not affiliated with OWASP or Ollama.
