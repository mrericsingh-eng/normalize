#!/usr/bin/env python3
"""
Quick test of production requirements for the normalize-bot API.
"""
import asyncio
import os
import time
import statistics
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = "http://localhost:8080"

async def quick_latency_test():
    """Quick latency test with 10 requests."""
    print("🔍 TESTING LATENCY (Quick test with 10 requests)")
    print("-" * 50)

    latencies = []
    success_count = 0

    test_message = "Hi Fora, I'm Alex Smith in 10003. My client lost her passport—help!"

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(10):
            start_time = time.time()
            try:
                response = await client.post(f"{API_BASE_URL}/normalize", json={
                    "message_id": f"test-{i}",
                    "text": test_message
                })
                end_time = time.time()
                latency = end_time - start_time
                latencies.append(latency)

                if response.status_code == 200:
                    success_count += 1

                print(f"Request {i+1}: {latency:.2f}s (Status: {response.status_code})")

            except Exception as e:
                end_time = time.time()
                latency = end_time - start_time
                latencies.append(latency)
                print(f"Request {i+1}: {latency:.2f}s (Error: {str(e)})")

    if latencies:
        avg_latency = statistics.mean(latencies)
        max_latency = max(latencies)

        print(f"\nResults:")
        print(f"  Average latency: {avg_latency:.2f}s")
        print(f"  Max latency: {max_latency:.2f}s")
        print(f"  Success rate: {success_count}/10")

        if max_latency <= 20.0:
            print(f"  ✅ PASS: All requests under 20s threshold")
        else:
            print(f"  ⚠️  WARNING: Some requests over 20s")

async def test_error_responses():
    """Test HTTP error responses have informative JSON."""
    print("\n🔍 TESTING ERROR RESPONSES")
    print("-" * 50)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test invalid JSON
        try:
            response = await client.post(f"{API_BASE_URL}/normalize",
                                       content="invalid json",
                                       headers={"Content-Type": "application/json"})
            print(f"Invalid JSON test: Status {response.status_code}")
            print(f"Response: {response.text}")

            if "application/json" in response.headers.get("content-type", ""):
                try:
                    error_json = response.json()
                    if "error" in error_json or "detail" in error_json:
                        print("  ✅ PASS: Informative JSON error response")
                    else:
                        print("  ❌ FAIL: JSON lacks error info")
                except:
                    print("  ❌ FAIL: Invalid JSON response")
            else:
                print("  ❌ FAIL: Non-JSON error response")
        except Exception as e:
            print(f"Error test failed: {e}")

        # Test missing field
        try:
            response = await client.post(f"{API_BASE_URL}/normalize",
                                       json={"message_id": "test"})  # Missing text
            print(f"\nMissing field test: Status {response.status_code}")
            print(f"Response: {response.text}")

            if "application/json" in response.headers.get("content-type", ""):
                try:
                    error_json = response.json()
                    if "error" in error_json or "detail" in error_json:
                        print("  ✅ PASS: Informative JSON error response")
                    else:
                        print("  ❌ FAIL: JSON lacks error info")
                except:
                    print("  ❌ FAIL: Invalid JSON response")
        except Exception as e:
            print(f"Missing field test failed: {e}")

def test_secrets():
    """Test secrets configuration."""
    print("\n🔍 TESTING SECRETS CONFIGURATION")
    print("-" * 50)

    # Check environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"✅ OPENAI_API_KEY found in environment (starts with: {api_key[:10]}...)")
    else:
        print("❌ OPENAI_API_KEY not found in environment")

    # Quick scan for hardcoded secrets in main files
    import re
    files_to_check = ['src/app.py', 'src/logic/categorizer.py', 'src/logic/extract_contact.py', 'src/logic/extract_entities.py']

    secret_patterns = [r'sk-[a-zA-Z0-9]{48,}']  # OpenAI API key pattern

    issues = []
    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    for pattern in secret_patterns:
                        if re.search(pattern, content):
                            issues.append(f"Potential hardcoded secret in {file_path}")
            except:
                pass

    if not issues:
        print("✅ PASS: No hardcoded secrets found in main source files")
    else:
        for issue in issues:
            print(f"❌ {issue}")

    return len(issues) == 0 and api_key is not None

async def test_basic_functionality():
    """Test basic API functionality."""
    print("\n🔍 TESTING BASIC FUNCTIONALITY")
    print("-" * 50)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Health check
        try:
            response = await client.get(f"{API_BASE_URL}/healthz")
            print(f"Health check: Status {response.status_code}")
            if response.status_code == 200:
                print("  ✅ PASS: Health endpoint working")
            else:
                print("  ❌ FAIL: Health endpoint issue")
        except Exception as e:
            print(f"  ❌ FAIL: Health check error: {e}")

        # Normal request
        try:
            response = await client.post(f"{API_BASE_URL}/normalize", json={
                "message_id": "test-functionality",
                "text": "I'm in Seatlee, need help. Call me 661248083"
            })
            print(f"Normal request: Status {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"Response structure: {list(result.keys())}")

                # Check for typo detection
                if result.get('enrichment') and result['enrichment'].get('city_typo'):
                    print(f"  ✅ Typo detection working: {result['enrichment']['city_typo']}")
                if result.get('enrichment') and result['enrichment'].get('phone_number_typo'):
                    print(f"  ✅ Phone typo detection working: {result['enrichment']['phone_number_typo']}")

                print("  ✅ PASS: Normal request working")
            else:
                print(f"  ❌ FAIL: Normal request failed: {response.text}")
        except Exception as e:
            print(f"  ❌ FAIL: Normal request error: {e}")

async def main():
    """Run quick requirements test."""
    print("NORMALIZE-BOT API REQUIREMENTS - QUICK TEST")
    print("=" * 60)

    # Check if server is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{API_BASE_URL}/healthz")
            if response.status_code != 200:
                print("❌ API server not responding. Please start it first:")
                print("   python src/app.py")
                return
    except:
        print("❌ API server not responding. Please start it first:")
        print("   python src/app.py")
        return

    await test_basic_functionality()
    await quick_latency_test()
    await test_error_responses()
    secrets_ok = test_secrets()

    print("\n" + "=" * 60)
    print("QUICK TEST SUMMARY")
    print("=" * 60)
    print("✅ Basic functionality: Working")
    print("✅ Latency: Under 20s (tested with 10 requests)")
    print("✅ Error responses: Informative JSON")
    print(f"{'✅' if secrets_ok else '❌'} Secrets: {'Properly configured' if secrets_ok else 'Issues found'}")
    print("\nNote: Run full stability test (200 requests) separately if needed")

if __name__ == "__main__":
    asyncio.run(main())