#!/usr/bin/env python3
"""Test script for Profile Builder API endpoints."""

import asyncio
import uvicorn
from mooaid.api import app
import httpx


async def test_profile_builder():
    """Test the profile builder API endpoints."""
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8000') as client:
        print("=" * 60)
        print("PROFILE BUILDER API TEST")
        print("=" * 60)
        
        # Test 1: Start session
        print("\n[TEST 1] Starting Profile Builder Session...")
        resp = await client.post('/profile-builder/start', json={'profile_name': 'testprofile'})
        data = resp.json()
        print(f"  Response: {data}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert 'session_id' in data, "Missing session_id"
        session_id = data['session_id']
        print("  ✅ PASSED")
        
        # Test 2: Get first question
        print("\n[TEST 2] Getting First Question...")
        resp = await client.post(f'/profile-builder/{session_id}/question')
        data = resp.json()
        print(f"  Question: {data['question'][:80]}...")
        print(f"  Category: {data['category']}")
        print(f"  Progress: {data['progress_percent']}%")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert 'question' in data, "Missing question"
        assert 'category' in data, "Missing category"
        print("  ✅ PASSED")
        
        # Test 3: Submit answer
        print("\n[TEST 3] Submitting Answer...")
        resp = await client.post(
            f'/profile-builder/{session_id}/answer',
            json={'answer': 'I love coding and building software tools'}
        )
        data = resp.json()
        print(f"  Summary: {data.get('summary', 'N/A')}")
        print(f"  Extracted: {list(data.get('extracted', {}).keys())}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert 'summary' in data, "Missing summary"
        assert 'extracted' in data, "Missing extracted"
        print("  ✅ PASSED")
        
        # Test 4: Get next question
        print("\n[TEST 4] Getting Next Question...")
        resp = await client.post(f'/profile-builder/{session_id}/question')
        data = resp.json()
        print(f"  Question: {data['question'][:80]}...")
        print(f"  Progress: {data['progress_percent']}%")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        print("  ✅ PASSED")
        
        # Test 5: Cancel session
        print("\n[TEST 5] Cancelling Session...")
        resp = await client.delete(f'/profile-builder/{session_id}')
        data = resp.json()
        print(f"  Response: {data}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        print("  ✅ PASSED")
        
        # Test 6: Verify session is gone
        print("\n[TEST 6] Verifying Session Cleanup...")
        resp = await client.delete(f'/profile-builder/{session_id}')
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("  ✅ PASSED")
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✅")
        print("=" * 60)


async def main():
    """Run the test server and tests."""
    # Start server in background task
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    
    # Run server in background
    server_task = asyncio.create_task(server.serve())
    
    # Wait for server to start
    await asyncio.sleep(2)
    
    try:
        # Run tests
        await test_profile_builder()
    finally:
        # Shutdown server
        server.should_exit = True
        await server_task


if __name__ == "__main__":
    asyncio.run(main())
