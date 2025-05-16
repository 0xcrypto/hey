from bs4 import BeautifulSoup
import click
from markdown import markdown

def strip_markdown(text):
    try:
        html = markdown(text)
        return ''.join(BeautifulSoup(html, "html.parser").findAll(text=True))
    except Exception:
        return text

def stream_and_echo(llm, prompt_str, process_chunk=None):
    return stream(
        llm,
        prompt_str,
        process_chunk=process_chunk,
        process_line=lambda x: click.echo(x, nl=False),
    )


def stream(llm, prompt_str, process_chunk=None, process_line=None):
    response = ""
    current_line = ""
    for chunk in llm.stream(prompt_str):
        response += chunk
        current_line += chunk
        if chunk.endswith("\n"):
            if process_chunk:
                processed = process_chunk(current_line)
            else:
                processed = current_line
            if process_line:
                process_line(processed)
                process_line("\n" * (chunk.count("\n") - 1))
            current_line = ""
    if current_line:
        if process_chunk:
            processed = process_chunk(current_line)
        else:
            processed = current_line
        click.echo(processed, nl=False)
    click.echo("")
    return response