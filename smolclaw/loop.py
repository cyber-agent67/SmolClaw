#!/usr/bin/env python3
"""Run-loop orchestrator for SMOL claw runtimes."""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List


HUGGINGFACE_BASE_URL = "https://router.huggingface.co/v1"
HUGGINGFACE_DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"


class CommandSource:
    """Pluggable command source for long-running loop mode."""

    def next_command(self) -> str | None:
        raise NotImplementedError


class StdinCommandSource(CommandSource):
    """Reads commands from terminal input."""

    def next_command(self) -> str | None:
        try:
            command = input("smolclaw> ").strip()
        except EOFError:
            return "exit"
        return command


@dataclass
class GatewayQueueCommandSource(CommandSource):
    """Polls newline-delimited commands from a queue file."""

    queue_file: str
    idle_sleep_seconds: float = 0.4
    _offset: int = 0

    def next_command(self) -> str | None:
        if not os.path.exists(self.queue_file):
            time.sleep(self.idle_sleep_seconds)
            return None

        with open(self.queue_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if self._offset >= len(lines):
            time.sleep(self.idle_sleep_seconds)
            return None

        command = lines[self._offset].strip()
        self._offset += 1
        return command


class TelegramCommandSource(CommandSource):
    """Reserved source for future Telegram gateway integration."""

    def next_command(self) -> str | None:
        raise NotImplementedError("Telegram source is not implemented yet.")


def parse_arguments():
    parser = argparse.ArgumentParser(description="SMOL claw navigation runtime")
    parser.add_argument("--url", default="https://www.google.com", help="Starting URL")
    parser.add_argument("--prompt", help="Natural language prompt")
    parser.add_argument("--output", default=os.path.join("data", "output.json"), help="Output JSON file path")
    parser.add_argument(
        "--runtime",
        choices=["smolclaw", "smolhand"],
        default="smolclaw",
        help="Execution runtime: smolclaw (browser agent) or smolhand (tool-calling)",
    )
    parser.add_argument(
        "--model-type",
        type=str,
        default="LiteLLMModel",
        help="Model loader type for browser-agent runtime",
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default="gpt-4o",
        help="Model ID for browser-agent runtime",
    )
    parser.add_argument(
        "--smolhand-model",
        type=str,
        default=HUGGINGFACE_DEFAULT_MODEL,
        help="Model name for smolhand runtime",
    )
    parser.add_argument(
        "--smolhand-base-url",
        type=str,
        default=HUGGINGFACE_BASE_URL,
        help="Base URL for smolhand OpenAI-compatible API",
    )
    parser.add_argument(
        "--smolhand-api-key",
        type=str,
        default="",
        help="API key for smolhand OpenAI-compatible API",
    )
    parser.add_argument(
        "--max-loops",
        type=int,
        default=4,
        help="Max tool loops per smolhand run",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="How many top-level run-loop iterations to execute",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue loop iterations after a failed attempt",
    )
    parser.add_argument(
        "--await-commands",
        action="store_true",
        help="Keep the agent running and await commands from a command source",
    )
    parser.add_argument(
        "--command-source",
        choices=["stdin", "gateway_queue", "telegram"],
        default="stdin",
        help="Command source used with --await-commands",
    )
    parser.add_argument(
        "--command-queue-file",
        default=os.path.join("data", "gateway_commands.queue"),
        help="Queue file path when --command-source gateway_queue is used",
    )
    return parser.parse_args()


def _ensure_output_dir(path: str) -> None:
    output_dir = os.path.dirname(path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)


def _load_smolhand_settings(args):
    from smolclaw.config import load_config

    cfg = load_config()
    model = args.smolhand_model or cfg.get("model", HUGGINGFACE_DEFAULT_MODEL)
    base_url = args.smolhand_base_url or cfg.get("base_url", HUGGINGFACE_BASE_URL)
    api_key = args.smolhand_api_key or cfg.get("api_key") or cfg.get("hf_token", "")
    return model, base_url, api_key


def _run_smolhand(args) -> Dict[str, Any]:
    from smolhand import OpenAICompatClient, SmolhandRunner, default_tools, ensure_connected_page

    model, base_url, api_key = _load_smolhand_settings(args)
    llm = OpenAICompatClient(model=model, base_url=base_url, api_key=api_key)
    runner = SmolhandRunner(llm_client=llm, tools=default_tools())
    connection_result = ensure_connected_page(args.url)

    prompt = args.prompt or "Summarize the current page"
    result = runner.run(prompt, max_loops=max(1, args.max_loops))
    return {
        "runtime": "smolhand",
        "model": model,
        "base_url": base_url,
        "start_url": args.url,
        "connection": connection_result,
        "prompt": prompt,
        "result": result,
    }


def _run_smolclaw(args):
    from smolclaw.agentic_runner import cleanup_resources, run_agent_with_args

    try:
        return run_agent_with_args(args)
    finally:
        cleanup_resources()


def _is_success(payload: Dict[str, Any]) -> bool:
    return isinstance(payload, dict) and not payload.get("error")


def _build_command_source(args) -> CommandSource:
    if args.command_source == "stdin":
        return StdinCommandSource()
    if args.command_source == "gateway_queue":
        return GatewayQueueCommandSource(queue_file=args.command_queue_file)
    if args.command_source == "telegram":
        return TelegramCommandSource()
    raise ValueError(f"Unsupported command source: {args.command_source}")


def execute_run_loop(args) -> Dict[str, Any]:
    iterations = max(1, int(args.iterations))
    attempts: List[Dict[str, Any]] = []

    for attempt_number in range(1, iterations + 1):
        try:
            if args.runtime == "smolhand":
                output = _run_smolhand(args)
            else:
                result = _run_smolclaw(args)
                output = result if result else {"error": "No result returned from agent"}

            attempts.append(
                {
                    "attempt": attempt_number,
                    "success": _is_success(output),
                    "output": output,
                }
            )

            if _is_success(output):
                break
        except Exception as exc:
            error_payload = {"error": str(exc), "runtime": args.runtime}
            attempts.append({"attempt": attempt_number, "success": False, "output": error_payload})
            if not args.continue_on_error:
                break

    final_attempt = attempts[-1]["output"] if attempts else {"error": "Run loop did not execute."}
    return {
        "runtime": args.runtime,
        "iterations_requested": iterations,
        "attempts_executed": len(attempts),
        "success": any(a["success"] for a in attempts),
        "attempts": attempts,
        "final": final_attempt,
    }


def await_commands_loop(args) -> Dict[str, Any]:
    """Keeps the agent process alive and runs commands until exit."""
    source = _build_command_source(args)
    history: List[Dict[str, Any]] = []

    while True:
        command = source.next_command()
        if command is None:
            continue

        normalized = command.strip()
        if not normalized:
            continue
        if normalized.lower() in {"exit", "quit", "stop"}:
            break

        run_args = argparse.Namespace(**vars(args))
        run_args.prompt = normalized
        run_result = execute_run_loop(run_args)
        history.append({"command": normalized, "result": run_result})

        print(json.dumps({"type": "command_result", "command": normalized, "result": run_result}, indent=2))

    return {
        "mode": "await_commands",
        "command_source": args.command_source,
        "commands_executed": len(history),
        "history": history,
        "final": history[-1]["result"] if history else {"message": "No commands executed."},
    }


def main():
    args = parse_arguments()
    if args.await_commands:
        output = await_commands_loop(args)
    else:
        output = execute_run_loop(args)

    _ensure_output_dir(args.output)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Results saved to {args.output}")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
