import typer
from rich import print

from repomind.core import (
    ensure, read, write, log, git_diff,
    read_config, write_config, read_chain, write_chain,
    read_history, append_history, write_history,
    CTX, DEC,
)
from repomind.providers import call_chain, REGISTRY
from repomind.providers.base import Message

app = typer.Typer()
fallback_app = typer.Typer(help="Manage the provider fallback chain.")
history_app = typer.Typer(help="Manage conversation history.")
app.add_typer(fallback_app, name="fallback")
app.add_typer(history_app, name="history")


def _call(prompt: str, max_tokens: int, via: str | None = None, stream: bool = True) -> str:
    """Build message list from history + current prompt, then walk the chain."""
    if via and via not in REGISTRY:
        print(f"[red]Unknown provider '{via}'. Valid: {list(REGISTRY.keys())}[/red]")
        raise typer.Exit(1)
    chain = read_chain()
    history = read_history()
    messages = [Message(role=m["role"], content=m["content"]) for m in history]
    messages.append(Message(role="user", content=prompt))
    return call_chain(messages=messages, max_tokens=max_tokens, chain=chain, via=via, stream=stream)


def compress_context(text):
    return _call(
        prompt=f"Summarize this codebase context:\n\n{text}",
        max_tokens=800,
        stream=False,
    )


@app.command()
def init():
    ensure()
    print("[green]REPOMIND initialized (.repomind/ created)[/green]")


@app.command()
def save(text: str):
    ensure()

    ctx = read(CTX)
    ctx += "\n" + text

    if len(ctx) > 12000:
        print("[yellow]Compressing context...[/yellow]")
        ctx = compress_context(ctx)

    write(CTX, ctx)
    print("[green]Saved[/green]")


@app.command()
def ask(
    prompt: str,
    via: str = typer.Option(None, "--via", help="Force a specific provider (e.g. openai, gemini)"),
):
    ensure()

    context = read(CTX)
    full_prompt = f"""You are working inside a codebase.

CONTEXT:
{context}

TASK:
{prompt}
"""

    print("\n[cyan]AI:[/cyan]\n")
    output = _call(prompt=full_prompt, max_tokens=1200, via=via)
    print()

    append_history("user", prompt)
    append_history("assistant", output)

    log("USER", prompt)
    log("AI", output)


@app.command()
def plan(task: str):
    ensure()

    context = read(CTX)
    full_prompt = f"""Create a structured plan.

Context:
{context}

Task:
{task}
"""

    output = _call(prompt=full_prompt, max_tokens=1200)
    print()
    log("PLAN", output)
    write(DEC, output)
    append_history("user", task)
    append_history("assistant", output)


@app.command()
def diff():
    ensure()

    d = git_diff()
    if not d.strip():
        print("[yellow]No git diff[/yellow]")
        return

    ctx = read(CTX)
    write(CTX, ctx + "\n\nGIT DIFF:\n" + d)

    print("[green]Git diff added to context[/green]")


@app.command()
def exec(task: str):
    ensure()

    context = read(CTX)
    full_prompt = f"""Execute this task step-by-step:

Context:
{context}

Task:
{task}
"""

    output = _call(prompt=full_prompt, max_tokens=1200)
    print()
    log("EXEC", output)
    append_history("user", task)
    append_history("assistant", output)


@history_app.command("clear")
def history_clear():
    """Clear the conversation history."""
    ensure()
    write_history([])
    print("[green]History cleared.[/green]")


@history_app.command("show")
def history_show():
    """Show the current conversation history."""
    ensure()
    history = read_history()
    if not history:
        print("[yellow]No history.[/yellow]")
        return
    for entry in history:
        role = "[cyan]USER[/cyan]" if entry["role"] == "user" else "[green]AI[/green]"
        print(f"\n{role}: {entry['content'][:200]}{'...' if len(entry['content']) > 200 else ''}")


@fallback_app.command("set")
def fallback_set(providers: list[str] = typer.Argument(..., help="Ordered provider names")):
    """Set the provider chain order. E.g: repomind fallback set claude_cli anthropic_api openai"""
    ensure()
    unknown = [p for p in providers if p not in REGISTRY]
    if unknown:
        print(f"[red]Unknown providers: {unknown}. Valid: {list(REGISTRY.keys())}[/red]")
        raise typer.Exit(1)
    write_chain(providers)
    print(f"[green]Chain set to:[/green] {' -> '.join(providers)}")


@fallback_app.command("show")
def fallback_show():
    """Show the current provider chain."""
    ensure()
    chain = read_chain()
    print(f"Provider chain: [bold]{' -> '.join(chain)}[/bold]")
