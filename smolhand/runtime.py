"""Small-LLM tool-calling runtime (JSON-first, ReAct fallback)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests


@dataclass
class ToolDefinition:
    """Describes a callable tool for prompting and validation."""

    name: str
    description: str
    parameters: Dict[str, Any]
    func: Callable[..., Any]

    def as_prompt_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class OpenAICompatClient:
    """Simple OpenAI-compatible chat client (works with Ollama /v1 endpoints)."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",
        timeout: int = 60,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        """Runs a chat completion call and returns the assistant text."""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "") or ""


class SmolhandRunner:
    """Executes tool-calling loop for small LLMs."""

    def __init__(self, llm_client: OpenAICompatClient, tools: List[ToolDefinition]):
        self.llm_client = llm_client
        self.tools = {tool.name: tool for tool in tools}

    def _build_system_prompt(self) -> str:
        tool_schemas = [tool.as_prompt_schema() for tool in self.tools.values()]
        return (
            "You are smolhand, a tool-using assistant.\n"
            "You can inspect and navigate browser tabs. When the current page seems dead, blank, or inaccessible, "
            "use the available tab tools and continue from another open live tab before giving up.\n"
            "When a tool is required, respond ONLY with valid JSON in this exact shape:\n"
            "{\n"
            '  "tool_call": {\n'
            '    "name": "<tool_name>",\n'
            '    "arguments": { ... }\n'
            "  }\n"
            "}\n"
            "If no tool is required, answer normally.\n"
            "Available tools JSON schema:\n"
            f"{json.dumps(tool_schemas, indent=2)}\n"
            "If previous output was invalid JSON, correct it and output JSON only."
        )

    def _parse_tool_call(self, text: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        # JSON-first parsing
        try:
            obj = json.loads(text)
            if isinstance(obj, dict) and "tool_call" in obj:
                tool_call = obj["tool_call"]
                if isinstance(tool_call, dict):
                    name = tool_call.get("name")
                    args = tool_call.get("arguments", {})
                    if isinstance(name, str) and isinstance(args, dict):
                        return name, args
        except Exception:
            pass

        # ReAct fallback parsing for weaker models
        action_match = re.search(r"^Action:\s*(.+)$", text, flags=re.MULTILINE)
        input_match = re.search(r"^Action Input:\s*(.+)$", text, flags=re.MULTILINE)
        if action_match and input_match:
            name = action_match.group(1).strip()
            raw_args = input_match.group(1).strip()
            try:
                args = json.loads(raw_args)
                if isinstance(args, dict):
                    return name, args
            except Exception:
                return name, {}

        return None, None

    def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        if name not in self.tools:
            return f"Tool error: unknown tool '{name}'."

        tool = self.tools[name]
        try:
            result = tool.func(**arguments)
            if isinstance(result, (dict, list)):
                return json.dumps(result, indent=2)
            return str(result)
        except Exception as e:
            return f"Tool error while executing '{name}': {str(e)}"

    def run(self, user_prompt: str, max_loops: int = 4) -> str:
        """Runs a complete tool-calling session and returns final answer."""
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_prompt},
        ]

        for _ in range(max_loops):
            assistant = self.llm_client.chat(messages, temperature=0.2)
            messages.append({"role": "assistant", "content": assistant})

            tool_name, tool_args = self._parse_tool_call(assistant)
            if tool_name is None:
                return assistant

            tool_result = self._execute_tool(tool_name, tool_args or {})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Tool result:\n"
                        f"{tool_result}\n\n"
                        "Now provide the best final user-facing answer."
                    ),
                }
            )

        return "Unable to produce final answer within tool loop limit."


def _map_parameter_type(raw_type: Any) -> str:
    mapping = {
        "string": "string",
        "str": "string",
        "integer": "integer",
        "int": "integer",
        "number": "number",
        "float": "number",
        "boolean": "boolean",
        "bool": "boolean",
        "array": "array",
        "object": "object",
    }
    if isinstance(raw_type, str):
        return mapping.get(raw_type.lower(), "string")
    return "string"


def _convert_tool_parameters(raw_parameters: Any) -> Dict[str, Any]:
    if not isinstance(raw_parameters, dict):
        return {"type": "object", "properties": {}, "required": []}

    properties: Dict[str, Any] = {}
    required: List[str] = []
    for argument_name, parameter in raw_parameters.items():
        if not isinstance(parameter, dict):
            properties[argument_name] = {"type": "string"}
            continue

        prop: Dict[str, Any] = {
            "type": _map_parameter_type(parameter.get("type")),
        }
        description = parameter.get("description")
        if description:
            prop["description"] = description

        properties[argument_name] = prop
        if not parameter.get("nullable", False) and not parameter.get("optional", False):
            required.append(argument_name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def _tool_definition_from_registry_tool(tool: Any) -> Optional[ToolDefinition]:
    name = getattr(tool, "name", None) or getattr(tool, "__name__", None)
    if not name:
        return None

    description = getattr(tool, "description", None) or getattr(tool, "__doc__", None) or name
    raw_parameters = getattr(tool, "inputs", None) or getattr(tool, "parameters", None) or {}

    return ToolDefinition(
        name=name,
        description=description.strip(),
        parameters=_convert_tool_parameters(raw_parameters),
        func=tool,
    )


def default_tools() -> List[ToolDefinition]:
    """Returns browser tools when available, with general-purpose fallbacks for standalone use."""

    try:
        from agentic_navigator.tools.ToolRegistry import ToolRegistry

        registry_definitions = []
        for registry_tool in ToolRegistry.get_all_tools():
            definition = _tool_definition_from_registry_tool(registry_tool)
            if definition is not None:
                registry_definitions.append(definition)

        if registry_definitions:
            return registry_definitions
    except Exception:
        pass

    def get_time() -> str:
        return datetime.utcnow().isoformat() + "Z"

    def echo(text: str) -> str:
        return text

    def fetch_url(url: str, max_chars: int = 4000) -> str:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text[:max_chars]

    return [
        ToolDefinition(
            name="fetch_url",
            description="Fetch the text content of a URL",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "max_chars": {"type": "integer"},
                },
                "required": ["url"],
            },
            func=fetch_url,
        ),
        ToolDefinition(
            name="get_time",
            description="Get current UTC time",
            parameters={"type": "object", "properties": {}, "required": []},
            func=get_time,
        ),
        ToolDefinition(
            name="echo",
            description="Echo text",
            parameters={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
            func=echo,
        ),
    ]
