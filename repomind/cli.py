import os
import typer
from rich import print
from anthropic import Anthropic

from repomind.core import (
    ensure, read, write, log, git_diff,
    CTX, DEC
)

app = typer.Typer()

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def select_model(task: str):
    task = task.lower()

    if any(k in task for k in ["refactor", "design", "optimize", "architecture"]):
        return "claude-3-5-sonnet-20240620"

    return "claude-3-haiku-20240307"


def compress_context(text):
    res = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=800,
        messages=[{
            "role": "user",
            "content": f"Summarize this codebase context:\n\n{text}"
        }],
    )
    return res.content[0].text


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
def ask(prompt: str):
    ensure()

    model = select_model(prompt)
    context = read(CTX)

    full_prompt = f"""
You are working inside a codebase.

CONTEXT:
{context}

TASK:
{prompt}
"""

    res = client.messages.create(
        model=model,
        max_tokens=1200,
        messages=[{"role": "user", "content": full_prompt}],
    )

    output = res.content[0].text

    print("\n[cyan]AI:[/cyan]\n")
    print(output)

    log("USER", prompt)
    log("AI", output)

    write(CTX, context + f"\n\nUSER: {prompt}\nAI: {output}")


@app.command()
def plan(task: str):
    ensure()

    context = read(CTX)

    res = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1200,
        messages=[{
            "role": "user",
            "content": f"""
Create a structured plan.

Context:
{context}

Task:
{task}
"""
        }],
    )

    output = res.content[0].text

    print(output)
    log("PLAN", output)
    write(DEC, output)


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

    res = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1200,
        messages=[{
            "role": "user",
            "content": f"""
Execute this task step-by-step:

Context:
{context}

Task:
{task}
"""
        }],
    )

    output = res.content[0].text

    print(output)
    log("EXEC", output)