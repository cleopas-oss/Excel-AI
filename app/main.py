import asyncio
import sys

from agent.llm_client import LLMClient
from agent.excel_agent import ExcelAgent
from mcp.excel_mcp_client import ExcelMCPClient


async def main():

    agent = ExcelAgent(
        mcp_client=ExcelMCPClient(),
        llm_client=LLMClient()
    )

    if not await agent.initialize():
        return 1

    print("\nExcel AI Agent Ready! (type 'exit' to quit)\n")

    while True:

        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ["exit", "quit", "q"]:
                break

            if not user_input:
                continue

            success, result = await agent.execute_with_retry(user_input)

            print(("✅" if success else "❌"), result)

        except KeyboardInterrupt:
            break

    await agent.mcp_client.close()
    await agent.llm_client.close()

    print("Goodbye!")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))






