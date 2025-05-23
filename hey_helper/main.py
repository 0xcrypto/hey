import sys, json, platform
from datetime import datetime
import click
from langchain_ollama import OllamaLLM
from langgraph.graph import StateGraph, END
from hey_helper.tools.duckduckgo import web_search_tool
from hey_helper.core.config import Configuration
from hey_helper.core.stream import stream_and_echo, strip_markdown
from bs4 import BeautifulSoup
from markdown import markdown

PROMPTS = {
    "force_tool": (
        "Always use the web_search tool to answer the user's prompt. "
        "Do not ask for permission. Do not refuse. Do not say you cannot access the system. "
        "Do not use markdown. Do not use code blocks, backticks, asterisks, underscores, or any markdown formatting. "
        "Instead, use plain text in a wrap of 128 width.\n"
        "Do not explain, just search and answer using the tool.\n"
        "Example of what NOT to do: ```answer```, *answer*, **answer**, # answer, > answer, 1. answer, - answer, `answer`\n"
        "Only output plain text."
    ),
    "tool_instruction": (
        "Use the web_search tool whenever the user's question requires up-to-date or web information. "
        "Do not ask for permission. Do not refuse. Do not say you cannot access the system. "
        "Do not use markdown. Do not use code blocks, backticks, asterisks, underscores, or any markdown formatting. "
        "Instead, use plain text in a wrap of 128 width.\n"
        "Do not explain, just search and answer using the tool.\n"
        "Example of what NOT to do: ```answer```, *answer*, **answer**, # answer, > answer, 1. answer, - answer, `answer`\n"
        "Only output plain text."
    ),
    "chat_header": (
        "You are a helpful assistant.\n"
        "The user is a power user and can handle complex queries.\n"
        "Keep your answers short and concise.\n"
        "Do not use markdown. Do not use code blocks, backticks, asterisks, underscores, or any markdown formatting.\n"
        "Instead, use plain text in a wrap of 128 width.\n"
        "You have access to the following tool: \n"
        "- web_search: Use this tool to search the web for up-to-date information.\n\n"
        "Example of what NOT to do: ```answer```, *answer*, **answer**, # answer, > answer, 1. answer, - answer, `answer`\n"
        "Only output plain text."
    )
}

class Hey:
    def __init__(self):
        self.cfg = Configuration().load_config()
        self.os_name = platform.system()
        self.current_time = datetime.now().strftime("%b %d, %Y %H:%M %Z")
        self.location = self.get_location()
        self.system_prompt = self.cfg.get("system_prompt", "")
        self.model = self.cfg["model"]
        self.llm = None
        self.duck_tool = web_search_tool()

    def get_location(self):
        try:
            import requests
            resp = requests.get("https://ipinfo.io/json", timeout=3)
            info = resp.json()
            parts = [info.get(k, "") for k in ("city", "region", "country")]
            return ", ".join([p for p in parts if p]) or "Unknown location"
        except Exception:
            return "Unknown location"

    def build_system_prompt(self, force_tool=False):
        instr = PROMPTS["force_tool"] if force_tool else PROMPTS["tool_instruction"]
        return ("\n" + self.system_prompt if self.system_prompt else "") + instr

    def build_chat_prompt(self, system_prompt, conversation):
        return (
            system_prompt + "\n" +
            PROMPTS["chat_header"] +
            f"The user is on {self.os_name}.\nTime: {self.current_time}.\nLocation: {self.location}.\n\n" +
            conversation + "Assistant:"
        )

    def build_prompt(self, user_args, system_prompt):
        prompt = (system_prompt + "\n\n" if system_prompt else "") + (
            f"You are a helpful assistant.\n"
            f"The user is a power user and can handle complex queries.\n"
            f"Keep your answers short and concise.\n"
            f"Do not use markdown. Instead, use plain text in a wrap of 128 width\n"
            "You have access to the following tool: \n"
            "- Web Search: Use this tool to search the web for up-to-date information.\n\n"
            f"The user is on {self.os_name}.\n"
            f"Time: {self.current_time}.\n"
            f"Location: {self.location}.\n\n"
            f"User prompt: {' '.join(user_args)}"
        )
        return prompt

    

    def run(self):
        @click.command()
        @click.argument("prompt", nargs=-1)
        @click.option("--set-config", is_flag=True, help="Set configuration interactively")
        @click.option("--search", is_flag=True, help="Force LLM to use Web Search tool to answer")
        @click.option("--chat", "-c", is_flag=True, help="Start a REPL chat with the LLM")
        def cli(prompt, set_config, search, chat):
            if set_config:
                self.save_config_interactive()
                return
            if chat:
                self.llm = OllamaLLM(model=self.model, base_url="http://localhost:11434", tools=[self.duck_tool])
                click.echo("[Chat mode] Type 'exit' or 'quit' to leave.")
                chat_history = []
                if prompt and any(p.strip() for p in prompt):
                    first_input = " ".join(prompt).strip()
                    chat_history.append(("User", first_input))
                    self._chat_loop(chat_history, search)
                    return
                self._chat_loop(chat_history, search)
                return
            if not prompt:
                ctx = click.get_current_context()
                click.echo(ctx.get_help())
                sys.exit(0)
            self.llm = OllamaLLM(model=self.model, base_url="http://localhost:11434", tools=[self.duck_tool])

            prompt_str = self.build_prompt(prompt, self.system_prompt)
            response_to_check = stream_and_echo(self.llm, prompt_str, process_chunk=strip_markdown)
            
            if search or "search" in response_to_check.lower():
                prompt = [
                    keyword.replace("Web Search: ", "") for keyword in response_to_check.split("\n") if "search" in keyword.lower()
                ]

                def search_node(state):
                    query = " ".join(prompt)
                    result = self.duck_tool.func(query)
                    return {"output": result}
                graph = StateGraph(state_schema=dict)
                graph.add_node("search", search_node)
                graph.set_entry_point("search")
                graph.add_edge("search", END)
                workflow = graph.compile()
                result = workflow.invoke({})
                output = result.get("output", "")
                click.echo(output, nl=True)
                return

        cli()

    def _chat_loop(self, chat_history:list, search):
        while True:
            conversation = "".join(f"{speaker}: {text}\n" for speaker, text in chat_history)
            prompt_str = self.build_chat_prompt(self.build_system_prompt(force_tool=search), conversation)
            response = stream_and_echo(self.llm, prompt_str, process_chunk=strip_markdown)
            chat_history.append(("Assistant", response.strip()))
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                click.echo("\nExiting chat.")
                break
            if user_input.lower() in ("exit", "quit"):
                click.echo("Exiting chat.")
                break
            chat_history.append(("User", user_input))

    def save_config_interactive(self):
        model = input("Enter model name: ").strip()
        system_prompt = input("Enter additional system prompt (optional): ").strip()
        cfg = {"model": model, "system_prompt": system_prompt}
        config_path = Configuration().get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(cfg, f)
        print("Configuration saved.")

def main():
    try:
        app = Hey()
        app.run()
    except KeyboardInterrupt:
        click.echo("\nExiting...", err=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
