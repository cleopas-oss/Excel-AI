#!/usr/bin/env python3
"""
Deep protocol investigation - Check what initialize response actually contains
"""

import requests
import json
import uuid

EXCEL_MCP_URL = "http://excel-mcp:8017/mcp"

FASTMCP_HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json"
}


def test_initialize_with_full_response():
    """Test initialize and capture complete response"""
    print("=" * 80)
    print("INITIALIZE REQUEST - Full Response Analysis")
    print("=" * 80)

    session_id = str(uuid.uuid4())

    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "debug-client",
                "version": "1.0.0"
            }
        }
    }

    print(f"\n1. CLIENT SENDS:")
    print(f"   Method: POST")
    print(f"   URL: {EXCEL_MCP_URL}?session={session_id}")
    print(f"   Headers: {json.dumps(FASTMCP_HEADERS, indent=6)}")
    print(f"   Body: {json.dumps(payload, indent=6)}")

    response = requests.post(
        f"{EXCEL_MCP_URL}?session={session_id}",
        headers=FASTMCP_HEADERS,
        json=payload,
        timeout=5
    )

    print(f"\n2. SERVER RESPONDS:")
    print(f"   Status Code: {response.status_code}")
    print(f"   Response Headers:")
    for key, value in response.headers.items():
        print(f"     {key}: {value}")

    print(f"\n3. RESPONSE BODY (Raw Text):")
    print(f"   {response.text}")

    print(f"\n4. RESPONSE BODY (Parsed):")
    try:
        response_json = response.json()
        print(json.dumps(response_json, indent=2))

        print(f"\n5. KEY FINDINGS:")
        print(f"   - Response type: JSON")
        if "result" in response_json:
            print(f"   - Contains 'result' key")
            result = response_json["result"]
            print(f"   - Result content: {json.dumps(result, indent=6)}")
            if isinstance(result, dict):
                print(f"   - Result keys: {list(result.keys())}")
                if "sessionId" in result:
                    print(f"   - Server provides sessionId: {result['sessionId']}")
                elif "session_id" in result:
                    print(f"   - Server provides session_id: {result['session_id']}")
                else:
                    print(f"   - Server does NOT provide a session ID in result")
        else:
            print(f"   - No 'result' key in response")

    except json.JSONDecodeError:
        print(f"   Could not parse as JSON (streaming response)")
        print(f"   Response appears to be Server-Sent Events format")

    print(f"\n6. COOKIES (if any):")
    if response.cookies:
        for cookie in response.cookies:
            print(f"   {cookie.name}: {cookie.value}")
    else:
        print(f"   No cookies set by server")

    return session_id


def test_persistence_with_cookies():
    """Test if using cookies helps with session persistence"""
    print("\n\n" + "=" * 80)
    print("TEST: Session Persistence with Cookies")
    print("=" * 80)

    session = requests.Session()  # Use session object to persist cookies

    session_id = str(uuid.uuid4())

    # Initialize with session object
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "debug-client",
                "version": "1.0.0"
            }
        }
    }

    print(f"\n1. Send INITIALIZE with requests.Session()")
    response = session.post(
        f"{EXCEL_MCP_URL}?session={session_id}",
        headers=FASTMCP_HEADERS,
        json=payload,
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    print(f"   Cookies after init: {dict(session.cookies)}")

    # Try create_workbook with same session
    print(f"\n2. Send CREATE_WORKBOOK with same session object")
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "create_workbook",
        "params": {
            "filepath": "test_session.xlsx"
        }
    }

    response = session.post(
        f"{EXCEL_MCP_URL}?session={session_id}",
        headers=FASTMCP_HEADERS,
        json=payload,
        stream=True,
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text}")
    else:
        print(f"   Success!")


def main():
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║           FastMCP Session Persistence Investigation              ║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝\n")

    try:
        # Deep dive into initialize response
        test_initialize_with_full_response()

        # Test with cookies/persistent session
        test_persistence_with_cookies()

        print("\n" + "=" * 80)
        print("ANALYSIS & NEXT STEPS")
        print("=" * 80)
        print("""
The key question: Does the initialize response contain a session ID?

Possibility 1: Server provides session ID in response
→ We must extract it and use it in subsequent requests
→ Update line 150-155 in main.py to print extracted session ID

Possibility 2: Server does NOT provide session ID in response
→ Server might not support session persistence across HTTP requests
→ Need to use different transport OR use persistent connection

Possibility 3: Session IDs are one-time use
→ Each request generates its own context, not reused
→ Might need to change approach entirely

Check the output above to determine which is true.
        """)

    except Exception as e:
        print(f"\nFATAL ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
