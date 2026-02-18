from typing import Tuple
import json

from agent.agent_state import AgentState
from agent.tool_registry import ToolRegistry
from agent.tool_normalizer import normalize_arguments
from agent.utils import extract_json_from_text
from agent.workspace_manager import (
    workspace,
    RecoverableWorkspaceError,
    FatalWorkspaceError,
)
from agent.default_sheet_guard import tool_requires_sheet


class ExcelAgent:

    MAX_RETRIES = 3

    def __init__(self, mcp_client, llm_client):
        self.mcp_client = mcp_client
        self.llm_client = llm_client
        self.tool_registry = ToolRegistry()
        self.state = AgentState()

    async def initialize(self):

        if not await self.mcp_client.initialize():
            return False

        tools = await self.mcp_client.list_tools()
        print(f"✓ MCP ready ({len(tools)} tools)")

        return await self.llm_client.initialize()

    # ----------------------------
    # Metadata safety
    # ----------------------------

    def _safe_parse_metadata(self, raw):
        """Always return dict metadata"""
        if isinstance(raw, dict):
            return raw

        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

        return {}

    # ----------------------------
    # Prompt construction
    # ----------------------------

    def build_prompt(self, user_input: str, error: str | None = None):

        schemas = self.build_tool_schema_prompt()

        error_section = ""
        if error:
            error_section = f"""
Previous attempt failed:
{error}

Correct the mistake and produce valid JSON.
"""

        return f"""
You are a deterministic Excel automation agent.

Rules:
- Always return valid JSON
- Use exact tool names
- Provide ALL required fields
- Never invent argument names

Tool schemas:
{schemas}

{error_section}

User request:
{user_input}

Return ONLY:

{{
  "tool_name": "...",
  "arguments": {{ ... }}
}}
"""

    def build_tool_schema_prompt(self):

        lines = []

        for tool, schema in self.tool_registry.TOOL_SCHEMAS.items():
            required = schema["required"]
            example = {field: "..." for field in required}
            lines.append(f"{tool}: {example}")

        return "\n".join(lines)

    # ----------------------------
    # LLM decision
    # ----------------------------

    async def get_llm_decision(self, prompt):

        success, response = await self.llm_client.call_llm(prompt)

        if not success:
            return False, None, None

        data = extract_json_from_text(response)

        if not data:
            return False, None, None

        return True, data.get("tool_name"), data.get("arguments", {})

    # ----------------------------
    # Helpers
    # ----------------------------

    async def execute_batch_worksheets(self, arguments):

        filepath = arguments["filepath"]
        names = arguments["sheet_names"]

        for name in names:
            success, result = await self.mcp_client.call_tool(
                "create_worksheet",
                {"filepath": filepath, "sheet_name": name},
            )

            if not success:
                return False, result

        return True, f"Created worksheets: {', '.join(names)}"

    async def execute_rename_workbook(self, arguments):

        new_path = workspace.rename_file(
            arguments["old_filepath"],
            arguments["new_filepath"],
        )

        self.state.set_active_workbook(new_path.name)

        return True, f"Renamed workbook to {new_path}"

    async def resolve_default_sheet(self, arguments):

        if "sheet_name" in arguments:
            return arguments

        filepath = arguments.get("filepath")
        if not filepath:
            return arguments

        success, metadata = await self.mcp_client.call_tool(
            "get_workbook_metadata",
            {"filepath": filepath},
        )

        if not success:
            return arguments

        metadata = self._safe_parse_metadata(metadata)
        sheets = metadata.get("sheets", [])

        if sheets:
            arguments["sheet_name"] = sheets[0]

        return arguments

    # ----------------------------
    # Execution loop
    # ----------------------------

    async def execute_with_retry(
        self,
        user_input: str
    ) -> Tuple[bool, str]:

        error = None

        # Acquire workspace lock
        await workspace.acquire_lock()

        try:

            for _ in range(self.MAX_RETRIES):

                prompt = self.build_prompt(user_input, error)

                success, tool_name, arguments = await self.get_llm_decision(prompt)

                if not success or not tool_name:
                    error = "LLM failed to produce valid JSON"
                    continue

                try:
                    # Pass tool_name so normalizer knows when to skip resolve
                    arguments = normalize_arguments(
                        arguments,
                        self.state,
                        tool_name,
                    )

                    arguments = await self.resolve_default_sheet(arguments)

                    valid, error = self.tool_registry.validate_tool_call(
                        tool_name,
                        arguments,
                    )

                    if tool_requires_sheet(tool_name) and "sheet_name" not in arguments:
                        error = "Tool requires sheet_name"
                        continue

                    if not valid:
                        continue

                    # ----------------------------
                    # Execute tool
                    # ----------------------------

                    if tool_name == "create_workbook":

                        # Workspace handles canonicalization + registration
                        full_path = workspace.register_file(
                            arguments["filepath"]
                        )

                        success, result = await self.mcp_client.call_tool(
                            tool_name,
                            {"filepath": str(full_path)},
                        )

                        if success:
                            self.state.set_active_workbook(full_path.name)

                    elif tool_name == "create_multiple_worksheets":

                        success, result = await self.execute_batch_worksheets(arguments)

                    elif tool_name == "rename_workbook":

                        success, result = await self.execute_rename_workbook(arguments)

                    else:

                        success, result = await self.mcp_client.call_tool(
                            tool_name,
                            arguments,
                        )

                    workspace.log_execution(
                        user_input,
                        tool_name,
                        arguments.get("filepath"),
                        arguments,
                        "success" if success else result,
                    )

                    if success:
                        return True, result

                    error = result

                except RecoverableWorkspaceError as e:
                    error = str(e)

                except FatalWorkspaceError as e:
                    return False, f"Fatal workspace error: {e}"

        finally:
            workspace.release_lock()

        return False, f"Max retries exceeded. Last error: {error}"





