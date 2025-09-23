#!/usr/bin/env python3
"""
Final test - run all test cases and show complete JSON output.
"""
import asyncio
import json
import httpx

API_BASE_URL = "http://localhost:8080"

# Test cases from the original requirements
TEST_CASES = [
    "Hi Fora, I'm Alex Smith (917-555-1234) in 10003. My client flies to Rome next week and just lost her passport—help!",
    "Hi Fora, I'm Alex. My client is flying next week and just lost her passport—help!",
    "my wallet was stolen in Paris last night",
    "flight in 3 h, need assistance",
    "planning Rome in October with a stay at Chapter Roma and maybe NYC",
    "I am going to eat at Randy's Pub in the 95463 zip code, and I need to get to the airport in 2 hours. Can you book me a flight?",
    "I am currently staying at Ritz Carlton in Germany. But I want to book another hotel ASAP. Can you help?",
    "I am Dr. Singh. Also known as Eric. I need some immediate help. Call me 661248083",
    "I'm in the 91355 zie code in Brlin, and I need to go to Mexico ASAP. Can you book me a flight?",
    "I'm in Ls Anglees, need to travel to Toronto. I am feeling very scared and want to leave immediately. Call me 818900600"
]

async def test_all_cases():
    """Test all cases and print complete JSON responses."""

    # Check if server is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{API_BASE_URL}/healthz")
            if response.status_code != 200:
                print("ERROR: API server not responding")
                return
    except:
        print("ERROR: API server not responding")
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, text in enumerate(TEST_CASES, 1):
            try:
                response = await client.post(f"{API_BASE_URL}/normalize", json={
                    "message_id": f"test-case-{i}",
                    "text": text
                })

                if response.status_code == 200:
                    result = response.json()
                    print(f"Test Case {i}:")
                    print(f"Text: \"{text}\"")
                    print("JSON Response:")
                    print(json.dumps(result, indent=2))
                    print()
                else:
                    print(f"Test Case {i} FAILED:")
                    print(f"Text: \"{text}\"")
                    print(f"Status: {response.status_code}")
                    print(f"Response: {response.text}")
                    print()

            except Exception as e:
                print(f"Test Case {i} ERROR: {e}")
                print()

if __name__ == "__main__":
    asyncio.run(test_all_cases())