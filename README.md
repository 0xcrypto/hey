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

Or clone this repository and install dependencies:
```sh
pip install -r requirements.txt
python -m playwright install
```

## Usage
Ask a question:
```sh
python main.py <your question or task>
```

Force web search (DuckDuckGo):
```sh
python main.py --search <your question>
```

Set config (model/system prompt):
```sh
python main.py --set-config
```

## Configuration
- The first run will create a config file in your OS user config directory.
- You can change the model or add a system prompt using `--set-config`.

## License
MIT
