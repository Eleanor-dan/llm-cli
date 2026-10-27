from __future__ import annotations
import argparse
import json
import logging
import sys

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from rich.console import Console

from .import __version__
from .config import Settings
from .errors import LLMError
from .llm import Completion, LLMClient
from .prompts import build_messages
from .usage import estimate_cost

console = Console()
err_console = Console(stderr = True)

def build_args()-> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog = "llm-cli",
        description="A minimal LLM command line client.",
    )

    parser.add_argument(
        "prompt",
        nargs="*",
        help="Prompt text. Use '-' or pipe stdin to read stdin.",
    )

    # -f 是短选项，--file 是长选项；argparse 会把值存到 args.file。
    parser.add_argument("-f", "--file", help="Read the prompt from a file.")

    # -s / --system；不传时默认是 None。
    parser.add_argument("-s", "--system", help="System prompt.")

    parser.add_argument("-m", "--model", help="Override the model name.")
    parser.add_argument("-t", "--temperature", type=float, help="0.0 - 2.0")
    parser.add_argument("--max-tokens", type=int, help="Maximum output tokens.")

    parser.add_argument("--stream", action="store_true", help="Stream tokens as they arrive.")
    parser.add_argument("--json", action="store_true", help="Print a JSON object.")
    parser.add_argument("--debug", action="store_true", help="Print usage and debug logs.")
    parser.add_argument("--show_config", action="store_true", help="Print resolved config and exit." )

    # action="version" 会在打印版本后自动退出程序。
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser

def read_prompt(args: argparse.Namespace)-> str:
    if args.file:
        return Path(args.file).read_text(encoding= "utf-8")
    if args.prompt:
        text = " ".join(args.prompt)
        return sys.stdin.read() if text == "-" else text
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""

def _overrides(args: argparse.Namespace) -> dict[str, Any]:
    """把命令行里可能为 None 的参数收集起来，交给 LLMClient 处理。"""
    return {
        "model": args.model,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }

def _print_json(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + '\n')

def main(
        argv: Sequence[str] | None = None,
        client_factory: Any = LLMClient,
)-> int:
    parser = build_args()
    args = parser.parse_args(argv)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    try:
        prompt = read_prompt(args).strip()
    except FileNotFoundError:
        err_console.print(f"[red]File not found: {args.file}[/red]")
        return 2
    except OSError as exc:
        err_console.print(f"[red]Cannot read input: {exc}[/red]")
        return 2
    if not prompt:
        err_console.print("[red]No prompt. Pass text, --file, or pipe stdin.[/red]")
        return 2

    settings = Settings()
    if not settings.api_key:
        err_console.print("[red]LLM_API_KEY is not set. Copy .env.example to .env.[/red]")
        return 2

    messages = build_messages(prompt, system=args.system)
    client = client_factory(settings)
    overrides = _overrides(args)
    try:

        completion: Completion = client.complete(messages, **overrides)
        cost = estimate_cost(completion.model, completion.prompt_tokens,completion.completion_tokens)

        if args.json:
            _print_json(
                {
                    "content": completion.content,
                    "model": completion.model,
                    "usage": {
                        "prompt_tokens": completion.prompt_tokens,
                        "completion_tokens": completion.completion_tokens,
                        "total_tokens": completion.total_tokens,
                    },
                    "cost_usd": cost,
                }
            )
        else:
            console.print(completion.content, markup=False, highlight=False)

            if args.debug:
                # f-string：在字符串前加 f，花括号里可以写表达式。
                # `cost or 0` 处理 cost 为 None 的情况。
                err_console.print(
                    f"[dim]model={completion.model} "
                    f"tokens={completion.total_tokens} "
                    f"cost=${cost or 0:.6f}[/dim]"
                )
        return 0
    except LLMError as exc:
        err_console.print(f"[red]{exc}[/red]")
        return 1
    except KeyboardInterrupt:
        # 用户按 Ctrl+C 时，Python 会抛 KeyboardInterrupt。
        err_console.print("\n[yellow]Interrupted.[/yellow]")
        return 130


