#!/usr/bin/env python3
"""
Debug script to investigate FastMCP streamable-http session handling.

This script tests various ways of passing session ID to identify
which method the server actually expects.
"""

import requests
import json
import uuid

EXCEL_MCP_URL = "http://excel-mcp:8017/mcp"

FASTMCP_HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json"
}


def test_initialize_request():
    """Test the initialize call to see full response"""
    print("=" * 70)
    print("TEST 1: Initialize Request")
    print("=" * 70)

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

    print(f"\nSession ID: {session_id}")
    print(f"Request URL: {EXCEL_MCP_URL}?session={session_id}")
    print(f"Request Headers: {FASTMCP_HEADERS}")
    print(f"Request Body: {json.dumps(payload, indent=2)}")

    response = requests.post(
        f"{EXCEL_MCP_URL}?session={session_id}",
        headers=FASTMCP_HEADERS,
        json=payload,
        timeout=5
    )

    print(f"\n>>> Response Status: {response.status_code}")
    print(f">>> Response Headers: {dict(response.headers)}")

    print(f"\n>>> Response Body:")
    print(response.text)

    try:
        response_json = response.json()
        print(f"\n>>> Response JSON (formatted):")
        print(json.dumps(response_json, indent=2))
        return session_id, response_json
    except:
        print(">>> Could not parse response as JSON")
        return session_id, None


def test_create_workbook_url_session(session_id):
    """Test create_workbook with session in URL"""
    print("\n" + "=" * 70)
    print("TEST 2: Create Workbook with Session in URL")
    print("=" * 70)

    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "create_workbook",
        "params": {
            "filepath": "test_debug.xlsx"
        }
    }

    print(f"\nSession ID: {session_id}")
    print(f"Request URL: {EXCEL_MCP_URL}?session={session_id}")
    print(f"Request Headers: {FASTMCP_HEADERS}")
    print(f"Request Body: {json.dumps(payload, indent=2)}")

    response = requests.post(
        f"{EXCEL_MCP_URL}?session={session_id}",
        headers=FASTMCP_HEADERS,
        json=payload,
        stream=True,
        timeout=10
    )

    print(f"\n>>> Response Status: {response.status_code}")
    print(f">>> Response Headers: {dict(response.headers)}")

    print(f"\n>>> Response Body:")
    print(response.text)

    try:
        response_json = response.json()
        print(f"\n>>> Response JSON (formatted):")
        print(json.dumps(response_json, indent=2))
    except:
        print(">>> Could not parse response as JSON")


def test_create_workbook_header_session(session_id):
    """Test create_workbook with session in header"""
    print("\n" + "=" * 70)
    print("TEST 3: Create Workbook with Session in X-Session-ID Header")
    print("=" * 70)

    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "create_workbook",
        "params": {
            "filepath": "test_debug2.xlsx"
        }
    }

    headers = {**FASTMCP_HEADERS, "X-Session-ID": session_id}

    print(f"\nSession ID: {session_id}")
    print(f"Request URL: {EXCEL_MCP_URL}")
    print(f"Request Headers: {headers}")
    print(f"Request Body: {json.dumps(payload, indent=2)}")

    response = requests.post(
        EXCEL_MCP_URL,
        headers=headers,
        json=payload,
        stream=True,
        timeout=10
    )

    print(f"\n>>> Response Status: {response.status_code}")
    print(f">>> Response Headers: {dict(response.headers)}")

    print(f"\n>>> Response Body:")
    print(response.text)

    try:
        response_json = response.json()
        print(f"\n>>> Response JSON (formatted):")
        print(json.dumps(response_json, indent=2))
    except:
        print(">>> Could not parse response as JSON")


def test_create_workbook_body_session(session_id):
    """Test create_workbook with session in request body"""
    print("\n" + "=" * 70)
    print("TEST 4: Create Workbook with Session ID in Request Body")
    print("=" * 70)

    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "create_workbook",
        "params": {
            "filepath": "test_debug3.xlsx",
            "session_id": session_id
        }
    }

    print(f"\nSession ID: {session_id}")
    print(f"Request URL: {EXCEL_MCP_URL}")
    print(f"Request Headers: {FASTMCP_HEADERS}")
    print(f"Request Body: {json.dumps(payload, indent=2)}")

    response = requests.post(
        EXCEL_MCP_URL,
        headers=FASTMCP_HEADERS,
        json=payload,
        stream=True,
        timeout=10
    )

    print(f"\n>>> Response Status: {response.status_code}")
    print(f">>> Response Headers: {dict(response.headers)}")

    print(f"\n>>> Response Body:")
    print(response.text)

    try:
        response_json = response.json()
        print(f"\n>>> Response JSON (formatted):")
        print(json.dumps(response_json, indent=2))
    except:
        print(">>> Could not parse response as JSON")


def main():
    """Run all tests"""
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║  MCP Protocol Debug - FastMCP Streamable-HTTP Session Handling  ║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝\n")

    try:
        # Test 1: Initialize
        session_id, init_response = test_initialize_request()

        # Test 2: Create Workbook with URL session
        test_create_workbook_url_session(session_id)

        # Test 3: Create Workbook with header session
        test_create_workbook_header_session(session_id)

        # Test 4: Create Workbook with body session
        test_create_workbook_body_session(session_id)

        print("\n" + "=" * 70)
        print("TESTS COMPLETE")
        print("=" * 70)
        print("\nAnalysis:")
        print("- Test 2 (URL session): Most likely to work with streamable-http")
        print("- Test 3 (Header session): May be ignored by FastMCP")
        print("- Test 4 (Body session): Tests if session can be in params")
        print("\nReview the responses above to determine which method works.")

    except Exception as e:
        print(f"\nFATAL ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
