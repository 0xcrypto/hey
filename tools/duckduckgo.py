import requests
import asyncio
import click
import textwrap
from langchain_ollama import OllamaLLM
from playwright.async_api import async_playwright
from langchain.tools import Tool

# Use a default config for the LLM, or import from config if needed
DEFAULT_MODEL = "gemma3"
DEFAULT_BASE_URL = "http://localhost:11434"

def extract_search_keywords(user_query, llm=None):
    if llm is None:
        llm = OllamaLLM(model=DEFAULT_MODEL, base_url=DEFAULT_BASE_URL)
    prompt = (
        "Prepare short and concise search queries from the user prompt.\n"
        "Return them as a comma-separated list, no explanations.\n\n"
        f"User query: {user_query}"
    )
    response = "".join([chunk for chunk in llm.stream(prompt)])
    keywords = [k.strip() for k in response.split(",") if k.strip()]
    return keywords if keywords else [user_query]

def summarize_results(results, query, llm=None):
    if llm is None:
        llm = OllamaLLM(model=DEFAULT_MODEL, base_url=DEFAULT_BASE_URL)
    wrapped = ["\n".join(textwrap.wrap(part, width=128)) for part in results]
    summary_input = "\n\n".join(wrapped)
    summary_prompt = (
        f"The user has asked a question: {query}\n"
        "Summarize the following web search results in a concise paragraph. "
        "Do not use markdown.\n\n" + summary_input
    )
    summary = "".join([chunk for chunk in llm.stream(summary_prompt)])
    click.echo(summary, nl=True)
    exit(0)

def fallback_search(query, llm=None):
    click.echo("[+] Searching DuckDuckGo for instant answers...", err=True)
    try:
        resp = requests.get(
            f"https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json&no_redirect=1&no_html=1",
            timeout=5
        )
        data = resp.json()
        instant = data.get("AbstractText") or data.get("Answer") or data.get("Definition")
        if instant:
            return f"[DuckDuckGo Instant Answer]:\n{instant}"
    except Exception:
        click.echo("[-] DuckDuckGo instant answer failed", err=True)
    if llm is None:
        llm = OllamaLLM(model=DEFAULT_MODEL, base_url=DEFAULT_BASE_URL)
    prompt = f"User prompt: {query}"
    response = "".join([chunk for chunk in llm.stream(prompt)])
    return response

def search_headless(query, llm=None):
    click.echo(f"[+] Searching for: {query}", err=True)
    results = []
    keywords = extract_search_keywords(query, llm=llm)
    for keyword in keywords:
        async def run():
            try:
                async with async_playwright() as p:
                    browser = None
                    for browser_type in [p.chromium, p.firefox, p.webkit]:
                        try:
                            browser = await browser_type.launch(headless=True)
                            break
                        except Exception:
                            continue
                    if not browser:
                        click.echo("[-] No supported browser found for Playwright. Please install at least one (chromium, firefox, or webkit). with playwright install <browser_type>", err=True)
                        return
                    page = await browser.new_page()
                    await page.goto(f"https://duckduckgo.com/?q={requests.utils.quote(keyword)}&t=h_&ia=web")
                    await asyncio.sleep(2)
                    anchors = await page.query_selector_all('a[data-testid="result-title-a"]')
                    click.echo(f"[+] Found {len(anchors)} links for '{keyword}'.", err=True)
                    urls = []
                    for a in anchors[:5]:
                        href = await a.get_attribute('href')
                        if href and href.startswith('http') and 'duckduckgo.com' not in href:
                            urls.append(href)
                    async def fetch_content(url):
                        try:
                            new_page = await browser.new_page()
                            await new_page.goto(url, timeout=4000)
                            click.echo(f"[>] Reading: {url}", err=True)
                            main = await new_page.query_selector('main')
                            if not main:
                                main = await new_page.query_selector('body')
                            text = await main.inner_text() if main else ''
                            text = text[:2000]
                            await new_page.close()
                            return text
                        except Exception:
                            click.echo(f"[-] Failed to read: {url}", err=True)
                            return ""
                    tasks = [fetch_content(url) for url in urls]
                    results.extend(await asyncio.gather(*tasks))
                    await browser.close()
            except Exception:
                click.echo("[-] Unexpected error during Playwright search", err=True)
                return ""
            if results:
                return summarize_results(results, query, llm=llm)
            return "No relevant results found."
        result = asyncio.run(run())
        if result != "No relevant results found.":
            return result
    results = fallback_search(query, llm=llm)
    return results

def headless_search_tool():
    def _search(query: str) -> str:
        return search_headless(query)
    return Tool(
        name="headless_search",
        func=_search,
        description="Search the web for up-to-date information using a headless browser."
    )

# Optionally, you can provide Tool wrappers for integration
