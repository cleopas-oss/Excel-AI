import asyncio
import json
import subprocess
import os
from typing import Optional, Dict, Tuple, List


class ExcelMCPClient:

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.initialized = False

    # -------------------------------------------------
    # Process lifecycle
    # -------------------------------------------------

    async def _start_process(self) -> bool:

        env = os.environ.copy()
        env["EXCEL_FILES_PATH"] = "/excel_files"

        self.process = subprocess.Popen(
            ["uvx", "excel-mcp-server", "stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env
        )

        return True

    async def initialize(self) -> bool:

        try:
            await self._start_process()

            init_msg = {
                "jsonrpc": "2.0",
                "id": "init",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "excel-ai-agent",
                        "version": "2.0.0"
                    }
                }
            }

            self.process.stdin.write(json.dumps(init_msg) + "\n")
            self.process.stdin.flush()

            line = await asyncio.to_thread(self.process.stdout.readline)

            if not line:
                return False

            resp = json.loads(line)

            if "error" in resp:
                return False

            self.initialized = True
            print("✓ Connected to MCP server")
            return True

        except Exception as e:
            print(f"✗ MCP init failed: {e}")
            return False

    async def _restart(self):
        print("⚠ MCP crashed — restarting...")
        await self.close()
        self.initialized = False
        await self.initialize()

    # -------------------------------------------------
    # List tools
    # -------------------------------------------------

    async def list_tools(self) -> Tuple[bool, List[Dict]]:

        if not self.initialized:
            return False, []

        msg = {
            "jsonrpc": "2.0",
            "id": "list_tools",
            "method": "tools/list",
            "params": {}
        }

        try:
            self.process.stdin.write(json.dumps(msg) + "\n")
            self.process.stdin.flush()

        except BrokenPipeError:
            await self._restart()
            return await self.list_tools()

        line = await asyncio.to_thread(self.process.stdout.readline)

        try:
            resp = json.loads(line)

            if "error" in resp:
                return False, []

            tools = resp.get("result", {}).get("tools", [])
            return True, tools

        except Exception as e:
            print(f"Tool listing failed: {e}")
            return False, []

    # -------------------------------------------------
    # Tool execution
    # -------------------------------------------------

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict
    ) -> Tuple[bool, str]:

        if not self.initialized:
            return False, "Client not initialized"

        msg = {
            "jsonrpc": "2.0",
            "id": "tool_call",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        try:
            self.process.stdin.write(json.dumps(msg) + "\n")
            self.process.stdin.flush()

        except BrokenPipeError:
            await self._restart()
            return await self.call_tool(tool_name, arguments)

        line = await asyncio.to_thread(self.process.stdout.readline)

        try:
            resp = json.loads(line)

            if "error" in resp:
                return False, str(resp["error"])

            result = resp.get("result", {})
            content = result.get("content", [{}])[0].get("text", "Success")

            if result.get("isError", False):
                return False, content

            return True, content

        except Exception as e:
            return False, str(e)

    # -------------------------------------------------
    # Shutdown
    # -------------------------------------------------

    async def close(self):

        if self.process:
            self.process.terminate()


