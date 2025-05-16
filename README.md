# Project: hey

Ask a question, get an answer—right in your terminal.

## Example
```
python main.py what was the command to list files in a directory
```

## Features
- Conversational AI for shell questions and tasks
- Runs on your machine with Ollama (Llama, Gemma, etc.)
- Customizable model and system prompt
- Web search via DuckDuckGo (headless browser)

## Requirements
- Ollama running locally (https://ollama.com/) with a model that supports tool usage. We recommend:
  - Gemma 3 - `ollama pull gemma3`
- Python 3.8+
- [playwright](https://playwright.dev/python/) (and browsers, see below)
- langchain, langchain-ollama, langgraph, click, requests

## Install & Setup
Install with [pipx](https://pypa.github.io/pipx/):
```sh
pipx install hey-helper
```

Or clone this repository and install locally with pipx:
```sh
pipx install .
```

## Usage
Ask a question:
```sh
hey <your question or task>
```

Force web search (DuckDuckGo):
```sh
hey --search <your question>
```

Set config (model/system prompt):
```sh
hey --set-config
```

## Configuration
- The first run will create a config file in your OS user config directory.
- You can change the model or add a system prompt using `--set-config`.

## License
MIT
