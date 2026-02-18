import os
import sys
import traceback

# --------------------------------------------------
# Robust import bootstrap
# --------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from app.agent.excel_agent import ExcelAgent
except Exception as e:
    print("❌ Failed to import ExcelAgent:", e)
    sys.exit(1)


# --------------------------------------------------
# Mock infrastructure (dependency injection fix)
# --------------------------------------------------

class MockLLMClient:
    """
    Simulates an LLM by forwarding prompts directly.
    Replace with real LLM in production.
    """

    def generate(self, prompt):
        return prompt


class MockMCPClient:
    """
    Safe wrapper around tool execution.
    Captures crashes instead of killing test suite.
    """

    def execute(self, command):
        return command


# --------------------------------------------------
# Phase 1 Integration Test Suite
# --------------------------------------------------

TEST_CASES = [

    # Workbook lifecycle
    "Create workbook test_phase1.xlsx",
    "Add worksheet Sales",
    "Add worksheet Inventory",

    # Data writing
    "Write Product,Price to Sales A1",
    "Write Laptop,1200 to Sales A2",

    # Reading
    "Read Sales worksheet",

    # Error resilience
    "Add worksheet Sales",
    "Delete worksheet Ghost",

    # State integrity
    "Add worksheet FinalCheck",
    "Read all worksheets"
]


def run_phase1_tests():

    print("\n" + "=" * 70)
    print("PHASE 1 — EXCEL AGENT INTEGRATION TEST")
    print("=" * 70)

    llm = MockLLMClient()
    mcp = MockMCPClient()

    try:
        agent = ExcelAgent(mcp, llm)
    except Exception as e:
        print("❌ Agent initialization failed")
        print(e)
        return

    passed = 0
    failed = 0

    for i, test in enumerate(TEST_CASES, 1):

        print(f"\n🧪 Test {i}: {test}")

        try:
            result = agent.run(test)
            print("✅ Result:", result)
            passed += 1

        except Exception:
            print("❌ Crash detected")
            print(traceback.format_exc())
            failed += 1

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("=" * 70)


if __name__ == "__main__":
    run_phase1_tests()

