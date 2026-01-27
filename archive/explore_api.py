#!/usr/bin/env python3
"""Explore Gaggimate API to find shot update endpoints."""

import asyncio
import json
from websockets import connect

async def explore_websocket():
    """Connect to WebSocket and listen for all message types."""
    url = "ws://gaggimate.local/ws"

    try:
        async with connect(url) as websocket:
            print(f"✅ Connected to {url}")
            print("📡 Listening for messages (will timeout after 10 seconds)...\n")

            # Send a test request to list profiles (known working)
            test_request = {
                "tp": "req:profiles:list",
                "rid": "explore-test-123"
            }
            await websocket.send(json.dumps(test_request))
            print(f"📤 Sent: {test_request}\n")

            # Listen for messages
            timeout = 10
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                    data = json.loads(message)
                    print(f"📥 Received message type: {data.get('tp')}")
                    print(f"   Full message: {json.dumps(data, indent=2)}\n")

            except asyncio.TimeoutError:
                print("⏱️  Timeout - no more messages")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 Exploring Gaggimate WebSocket API\n")
    print("Looking for shot-related messages like:")
    print("  - req:shots:* / res:shots:*")
    print("  - req:history:* / res:history:*")
    print("  - evt:shot:* (events)")
    print("")

    asyncio.run(explore_websocket())
