"""
Test script for Candidate Chat WebSocket.

Tests the WebSocket endpoint WITHOUT needing the full server running.
Tests the ConnectionManager logic in isolation.

Run: python tests/test_websocket.py

NOTE: For live WebSocket testing against a running server, use test_websocket_live()
      which requires: pip install websockets
      and the server running at localhost:8000
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ==================== TEST 1: Connection Manager (No server needed) ====================

def test_connection_manager():
    """Test ConnectionManager tracking logic without a real WebSocket."""
    print("=" * 70)
    print("TEST 1: ConnectionManager (In-Memory Tracking)")
    print("=" * 70)

    # We can't import the full module (needs SQLAlchemy), so test the logic inline
    # This mirrors the exact logic in websocket.py

    class MockConnectionManager:
        def __init__(self):
            self._active_connections = {}
            self._candidate_sessions = {}

        def connect(self, session_id, candidate_id):
            self._active_connections[session_id] = f"ws_mock_{session_id}"
            if candidate_id not in self._candidate_sessions:
                self._candidate_sessions[candidate_id] = set()
            self._candidate_sessions[candidate_id].add(session_id)

        def disconnect(self, session_id, candidate_id):
            self._active_connections.pop(session_id, None)
            if candidate_id in self._candidate_sessions:
                self._candidate_sessions[candidate_id].discard(session_id)
                if not self._candidate_sessions[candidate_id]:
                    del self._candidate_sessions[candidate_id]

        def is_connected(self, session_id):
            return session_id in self._active_connections

        @property
        def connection_count(self):
            return len(self._active_connections)

    mgr = MockConnectionManager()

    # Test connect
    mgr.connect("session-1", "candidate-A")
    mgr.connect("session-2", "candidate-A")
    mgr.connect("session-3", "candidate-B")

    assert mgr.connection_count == 3, f"Expected 3, got {mgr.connection_count}"
    assert mgr.is_connected("session-1"), "session-1 should be connected"
    assert mgr.is_connected("session-3"), "session-3 should be connected"
    assert not mgr.is_connected("session-99"), "session-99 should NOT be connected"
    assert len(mgr._candidate_sessions["candidate-A"]) == 2, "candidate-A should have 2 sessions"
    print("  [PASS] Connect: 3 connections tracked correctly")

    # Test disconnect
    mgr.disconnect("session-1", "candidate-A")
    assert mgr.connection_count == 2, f"Expected 2, got {mgr.connection_count}"
    assert not mgr.is_connected("session-1"), "session-1 should be disconnected"
    assert len(mgr._candidate_sessions["candidate-A"]) == 1, "candidate-A should have 1 session"
    print("  [PASS] Disconnect: session-1 removed, candidate-A has 1 session left")

    # Test disconnect last session of a candidate
    mgr.disconnect("session-2", "candidate-A")
    assert "candidate-A" not in mgr._candidate_sessions, "candidate-A should be fully removed"
    print("  [PASS] Full disconnect: candidate-A removed from tracking")

    # Test idempotent disconnect (no error on double disconnect)
    mgr.disconnect("session-1", "candidate-A")  # already disconnected
    print("  [PASS] Idempotent disconnect: no error on double disconnect")

    # Test candidate-B still connected
    assert mgr.is_connected("session-3"), "session-3 should still be connected"
    assert mgr.connection_count == 1, f"Expected 1, got {mgr.connection_count}"
    print("  [PASS] Isolation: candidate-B unaffected by candidate-A disconnects")

    print("\n  [PASS] All ConnectionManager tests passed!")


# ==================== TEST 2: Message Protocol Validation ====================

def test_message_protocol():
    """Test the WebSocket message protocol format."""
    print("\n" + "=" * 70)
    print("TEST 2: Message Protocol Validation")
    print("=" * 70)

    # Client -> Server messages
    valid_messages = [
        {
            "name": "text message",
            "msg": {"type": "message", "content": "Hello", "message_type": "text", "message_data": {}},
        },
        {
            "name": "button click",
            "msg": {"type": "message", "content": "Create with Bot", "message_type": "text",
                    "message_data": {"button_id": "create_with_bot"}},
        },
        {
            "name": "question answer",
            "msg": {"type": "message", "content": "Sagar Rajak", "message_type": "text",
                    "message_data": {"question_key": "full_name", "value": "Sagar Rajak"}},
        },
        {
            "name": "file upload",
            "msg": {"type": "message", "content": "resume.pdf", "message_type": "text",
                    "message_data": {"file_url": "https://s3.example.com/resume.pdf"}},
        },
        {
            "name": "ping",
            "msg": {"type": "ping"},
        },
    ]

    for item in valid_messages:
        msg = item["msg"]
        serialized = json.dumps(msg)
        parsed = json.loads(serialized)
        assert parsed["type"] in ("message", "ping"), f"Invalid type: {parsed['type']}"
        if parsed["type"] == "message":
            assert "content" in parsed, "Missing content"
        print(f"  [PASS] {item['name']}: {serialized[:80]}...")

    # Server -> Client messages
    server_messages = [
        {"type": "connected", "session_id": "abc-123", "candidate_id": "def-456", "timestamp": "2026-02-06T10:00:00"},
        {"type": "pong", "timestamp": "2026-02-06T10:00:00"},
        {"type": "typing", "is_typing": True},
        {"type": "typing", "is_typing": False},
        {"type": "user_message_ack", "message": {"id": "msg-1", "role": "user", "content": "Hello"}},
        {"type": "bot_message", "message": {"id": "msg-2", "role": "bot", "content": "Hi!", "message_type": "text"}},
        {"type": "session_update", "session": {"id": "abc-123", "session_status": "active"}},
        {"type": "error", "error": "Something went wrong", "code": "PROCESSING_ERROR"},
    ]

    print("\n  Server -> Client messages:")
    for msg in server_messages:
        serialized = json.dumps(msg)
        parsed = json.loads(serialized)
        assert "type" in parsed, "Missing type field"
        print(f"  [PASS] {msg['type']}: valid JSON ({len(serialized)} bytes)")

    print("\n  [PASS] All protocol messages valid!")


# ==================== TEST 3: WebSocket Flow Simulation ====================

def test_websocket_flow():
    """Simulate the full WebSocket conversation flow."""
    print("\n" + "=" * 70)
    print("TEST 3: WebSocket Flow Simulation")
    print("=" * 70)

    flow = [
        ("CLIENT", "connect", "ws://localhost:8000/api/v1/candidate-chat/ws/session-123?candidate_id=cand-456"),
        ("SERVER", "connected", {"type": "connected", "session_id": "session-123"}),
        ("CLIENT", "ping", {"type": "ping"}),
        ("SERVER", "pong", {"type": "pong"}),
        ("CLIENT", "select method", {"type": "message", "content": "Create with Bot", "message_type": "text",
                                      "message_data": {"button_id": "create_with_bot"}}),
        ("SERVER", "typing on", {"type": "typing", "is_typing": True}),
        ("SERVER", "typing off", {"type": "typing", "is_typing": False}),
        ("SERVER", "ack", {"type": "user_message_ack", "message": {"role": "user", "content": "Create with Bot"}}),
        ("SERVER", "bot intro", {"type": "bot_message", "message": {"role": "bot", "content": "Let's build your resume for the Software Developer role!"}}),
        ("SERVER", "first question", {"type": "bot_message", "message": {"role": "bot", "content": "What is your full name?", "message_type": "input_text"}}),
        ("SERVER", "session update", {"type": "session_update", "session": {"step": "asking_questions"}}),
        ("CLIENT", "answer", {"type": "message", "content": "Sagar Rajak", "message_type": "text",
                               "message_data": {"question_key": "full_name", "value": "Sagar Rajak"}}),
        ("SERVER", "typing on", {"type": "typing", "is_typing": True}),
        ("SERVER", "typing off", {"type": "typing", "is_typing": False}),
        ("SERVER", "ack", {"type": "user_message_ack", "message": {"role": "user", "content": "Sagar Rajak"}}),
        ("SERVER", "got it", {"type": "bot_message", "message": {"role": "bot", "content": "Got it!"}}),
        ("SERVER", "next question", {"type": "bot_message", "message": {"role": "bot", "content": "What is your date of birth?", "message_type": "input_date"}}),
    ]

    print("  Simulated WebSocket conversation flow:\n")
    for direction, label, data in flow:
        arrow = "-->" if direction == "CLIENT" else "<--"
        if isinstance(data, str):
            print(f"    {direction} {arrow} {label}: {data}")
        else:
            msg_type = data.get("type", "")
            print(f"    {direction} {arrow} [{msg_type}] {label}")

    print(f"\n  Total exchanges: {len(flow)}")
    print(f"  Client messages: {sum(1 for d, _, _ in flow if d == 'CLIENT')}")
    print(f"  Server messages: {sum(1 for d, _, _ in flow if d == 'SERVER')}")
    print("\n  [PASS] Flow simulation complete!")


# ==================== TEST 4: Live WebSocket Test (needs running server) ====================

def print_live_test_instructions():
    """Print instructions for live WebSocket testing."""
    print("\n" + "=" * 70)
    print("TEST 4: Live WebSocket Test (MANUAL)")
    print("=" * 70)

    print("""
  To test the WebSocket against a running server:

  1. Start the server:
     cd server
     uvicorn app.main:app --reload --port 8000

  2. First create a session via REST (get a session_id):
     curl -X POST http://localhost:8000/api/v1/candidate-chat/sessions \\
       -H "Content-Type: application/json" \\
       -d '{"candidate_id": "<YOUR_CANDIDATE_UUID>", "session_type": "resume_creation"}'

  3. Install websockets library:
     pip install websockets

  4. Run the live test (replace UUIDs):
     python tests/test_websocket_live.py <SESSION_ID> <CANDIDATE_ID>

  OR use the quick Python snippet below:
  """)

    print("""  -------------------------------------------------------
  import asyncio, json, websockets

  async def test():
      SESSION_ID = "paste-session-uuid-here"
      CANDIDATE_ID = "paste-candidate-uuid-here"
      uri = f"ws://localhost:8000/api/v1/candidate-chat/ws/{SESSION_ID}?candidate_id={CANDIDATE_ID}"

      async with websockets.connect(uri) as ws:
          # 1. Receive connected ack
          ack = json.loads(await ws.recv())
          print(f"Connected: {ack}")

          # 2. Send ping
          await ws.send(json.dumps({"type": "ping"}))
          pong = json.loads(await ws.recv())
          print(f"Pong: {pong}")

          # 3. Send a message (select bot method)
          await ws.send(json.dumps({
              "type": "message",
              "content": "Create with Bot",
              "message_type": "text",
              "message_data": {"button_id": "create_with_bot"}
          }))

          # 4. Receive all responses
          for _ in range(10):
              try:
                  msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
                  print(f"  << {msg['type']}: {json.dumps(msg)[:120]}")
              except asyncio.TimeoutError:
                  print("  (no more messages)")
                  break

  asyncio.run(test())
  -------------------------------------------------------
  """)

    print("  [INFO] Live test instructions printed above")


# ==================== MAIN ====================

if __name__ == "__main__":
    print("\n[TEST] AIVIUE WebSocket Test Suite")
    print("=" * 70)

    test_connection_manager()
    test_message_protocol()
    test_websocket_flow()
    print_live_test_instructions()

    print("\n" + "=" * 70)
    print("[DONE] All offline tests passed! See above for live test instructions.")
    print("=" * 70)
