#!/usr/bin/env python3
"""
Test the production requirements for the normalize-bot API.

Requirements tested:
1. Latency p95 ≤ 20s (NYC → endpoint)
2. Stability: 200 sequential requests, < 1% non-2xx
3. HTTP errors: Informative JSON bodies
4. Secrets: Only via environment variables
"""
import asyncio
import os
import time
import statistics
import json
from typing import List, Dict, Any
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test configuration
API_BASE_URL = "http://localhost:8080"
TEST_REQUESTS = 200
LATENCY_THRESHOLD_SECONDS = 20.0

# Test messages for requests
TEST_MESSAGES = [
    "Hi Fora, I'm Alex Smith (917-555-1234) in 10003. My client flies to Rome next week and just lost her passport—help!",
    "my wallet was stolen in Paris last night",
    "flight in 3 h, need assistance",
    "I am Dr. Smith. Also known as Tommy. I need some immediate help. Call me 661248083",
    "I'm in Seatlee, need to travel to Vancouver. I am feeling very scared and want to leave immediately.",
    "planning Rome in October with a stay at Chapter Roma",
    "I am going to eat at Olive Garden in the 48410 zip code, and I need to get to the airport in 2 hours."
]

async def test_latency_requirement():
    """Test latency p95 ≤ 20s requirement."""
    print("=" * 60)
    print("TESTING LATENCY REQUIREMENT (p95 ≤ 20s)")
    print("=" * 60)

    latencies = []
    success_count = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(50):  # Test with 50 requests for p95 calculation
            message = TEST_MESSAGES[i % len(TEST_MESSAGES)]

            start_time = time.time()
            try:
                response = await client.post(f"{API_BASE_URL}/normalize", json={
                    "message_id": f"test-latency-{i}",
                    "text": message
                })
                end_time = time.time()
                latency = end_time - start_time
                latencies.append(latency)

                if response.status_code == 200:
                    success_count += 1

                print(f"Request {i+1}/50: {latency:.2f}s (Status: {response.status_code})")

            except Exception as e:
                end_time = time.time()
                latency = end_time - start_time
                latencies.append(latency)
                print(f"Request {i+1}/50: {latency:.2f}s (Error: {str(e)})")

    # Calculate statistics
    if latencies:
        p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        avg_latency = statistics.mean(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)

        print(f"\nLATENCY RESULTS:")
        print(f"  Requests completed: {len(latencies)}")
        print(f"  Successful responses: {success_count}")
        print(f"  Average latency: {avg_latency:.2f}s")
        print(f"  Min latency: {min_latency:.2f}s")
        print(f"  Max latency: {max_latency:.2f}s")
        print(f"  P95 latency: {p95_latency:.2f}s")
        print(f"  Threshold: {LATENCY_THRESHOLD_SECONDS}s")

        if p95_latency <= LATENCY_THRESHOLD_SECONDS:
            print(f"  ✅ PASS: P95 latency ({p95_latency:.2f}s) ≤ {LATENCY_THRESHOLD_SECONDS}s")
            return True
        else:
            print(f"  ❌ FAIL: P95 latency ({p95_latency:.2f}s) > {LATENCY_THRESHOLD_SECONDS}s")
            return False
    else:
        print("  ❌ FAIL: No latency data collected")
        return False

async def test_stability_requirement():
    """Test stability: 200 sequential requests, < 1% non-2xx."""
    print("\n" + "=" * 60)
    print("TESTING STABILITY REQUIREMENT (200 requests, < 1% non-2xx)")
    print("=" * 60)

    success_count = 0
    error_count = 0
    status_codes = {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(TEST_REQUESTS):
            message = TEST_MESSAGES[i % len(TEST_MESSAGES)]

            try:
                response = await client.post(f"{API_BASE_URL}/normalize", json={
                    "message_id": f"test-stability-{i}",
                    "text": message
                })

                status_code = response.status_code
                status_codes[status_code] = status_codes.get(status_code, 0) + 1

                if 200 <= status_code < 300:
                    success_count += 1
                else:
                    error_count += 1
                    print(f"Request {i+1}: Non-2xx response {status_code}")

                if (i + 1) % 10 == 0:
                    success_rate_so_far = (success_count / (i + 1)) * 100
                    print(f"Progress: {i+1}/{TEST_REQUESTS} requests completed - Success rate: {success_rate_so_far:.1f}%")

            except Exception as e:
                error_count += 1
                print(f"Request {i+1}: Exception - {str(e)}")

    # Calculate results
    error_rate = (error_count / TEST_REQUESTS) * 100
    success_rate = (success_count / TEST_REQUESTS) * 100

    print(f"\nSTABILITY RESULTS:")
    print(f"  Total requests: {TEST_REQUESTS}")
    print(f"  Successful (2xx): {success_count}")
    print(f"  Non-2xx/Errors: {error_count}")
    print(f"  Success rate: {success_rate:.1f}%")
    print(f"  Error rate: {error_rate:.1f}%")
    print(f"  Status code breakdown: {status_codes}")

    if error_rate < 1.0:
        print(f"  ✅ PASS: Error rate ({error_rate:.1f}%) < 1%")
        return True
    else:
        print(f"  ❌ FAIL: Error rate ({error_rate:.1f}%) ≥ 1%")
        return False

async def test_http_errors_requirement():
    """Test HTTP errors have informative JSON bodies."""
    print("\n" + "=" * 60)
    print("TESTING HTTP ERRORS REQUIREMENT (Informative JSON bodies)")
    print("=" * 60)

    test_cases = [
        {
            "name": "Invalid JSON body",
            "data": "invalid json",
            "headers": {"Content-Type": "application/json"}
        },
        {
            "name": "Missing required field",
            "data": {"message_id": "test-error-1"},  # Missing 'text' field
            "headers": {"Content-Type": "application/json"}
        },
        {
            "name": "Invalid data types",
            "data": {"message_id": 123, "text": ["not", "a", "string"]},
            "headers": {"Content-Type": "application/json"}
        }
    ]

    all_passed = True

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, test_case in enumerate(test_cases):
            print(f"\nTest {i+1}: {test_case['name']}")

            try:
                if isinstance(test_case['data'], str):
                    # Send raw string for invalid JSON test
                    response = await client.post(
                        f"{API_BASE_URL}/normalize",
                        content=test_case['data'],
                        headers=test_case['headers']
                    )
                else:
                    response = await client.post(f"{API_BASE_URL}/normalize", json=test_case['data'])

                print(f"  Status Code: {response.status_code}")

                # Check if response has JSON content type
                content_type = response.headers.get("content-type", "")
                if "application/json" not in content_type:
                    print(f"  ❌ FAIL: Response not JSON (Content-Type: {content_type})")
                    all_passed = False
                    continue

                # Try to parse JSON response
                try:
                    error_body = response.json()
                    print(f"  Response body: {json.dumps(error_body, indent=2)}")

                    # Check if error body is informative
                    if isinstance(error_body, dict):
                        has_error_field = "error" in error_body
                        has_detail_field = "detail" in error_body

                        if has_error_field or has_detail_field:
                            print(f"  ✅ PASS: Informative JSON error body")
                        else:
                            print(f"  ❌ FAIL: JSON body lacks error information")
                            all_passed = False
                    else:
                        print(f"  ❌ FAIL: JSON body is not an object")
                        all_passed = False

                except json.JSONDecodeError:
                    print(f"  ❌ FAIL: Response body is not valid JSON")
                    all_passed = False

            except Exception as e:
                print(f"  ❌ FAIL: Exception during request - {str(e)}")
                all_passed = False

    if all_passed:
        print(f"\n  ✅ PASS: All HTTP errors have informative JSON bodies")
    else:
        print(f"\n  ❌ FAIL: Some HTTP errors lack informative JSON bodies")

    return all_passed

def test_secrets_requirement():
    """Test secrets are only via environment variables."""
    print("\n" + "=" * 60)
    print("TESTING SECRETS REQUIREMENT (Only via environment variables)")
    print("=" * 60)

    issues_found = []

    # Check if API key is in environment
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"✅ OPENAI_API_KEY found in environment (starts with: {api_key[:10]}...)")
    else:
        issues_found.append("OPENAI_API_KEY not found in environment")

    # Check source code for hardcoded secrets (basic scan)
    import re

    secret_patterns = [
        r'sk-[a-zA-Z0-9]{32,}',  # OpenAI API keys
        r'OPENAI_API_KEY\s*=\s*["\'][^"\']+["\']',  # Hardcoded API key assignments
        r'api[_-]?key\s*=\s*["\'][^"\']+["\']',  # Generic API key assignments
    ]

    source_files = []
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                source_files.append(os.path.join(root, file))

    print(f"\nScanning {len(source_files)} source files for hardcoded secrets...")

    for file_path in source_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                for pattern in secret_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # Check if it's just a reference to environment variable (not hardcoded)
                        for match in matches:
                            if 'os.getenv' not in content or 'sk-' in match:
                                issues_found.append(f"Potential hardcoded secret in {file_path}: {match[:20]}...")
        except Exception as e:
            print(f"Warning: Could not scan {file_path}: {e}")

    # Check .env file contains secrets (this is OK for development)
    env_file_path = '.env'
    if os.path.exists(env_file_path):
        print(f"✅ .env file found for development configuration")

    if not issues_found:
        print(f"✅ PASS: No hardcoded secrets found, using environment variables properly")
        return True
    else:
        print(f"❌ FAIL: Issues found:")
        for issue in issues_found:
            print(f"  - {issue}")
        return False

async def start_api_server():
    """Start the API server for testing."""
    print("Starting API server...")

    # Check if server is already running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{API_BASE_URL}/healthz")
            if response.status_code == 200:
                print("✅ API server is already running")
                return True
    except:
        pass

    # Start server in background
    import subprocess
    import sys

    # Use the virtual environment Python
    venv_python = "venv/bin/python" if os.path.exists("venv/bin/python") else sys.executable

    try:
        process = subprocess.Popen([
            venv_python, "src/app.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Wait a bit for server to start
        await asyncio.sleep(3)

        # Check if server is responding
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{API_BASE_URL}/healthz")
            if response.status_code == 200:
                print("✅ API server started successfully")
                return True
            else:
                print(f"❌ API server not responding properly (status: {response.status_code})")
                return False

    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return False

async def main():
    """Run all requirement tests."""
    print("NORMALIZE-BOT API REQUIREMENTS TESTING")
    print("=" * 60)

    # Test secrets first (doesn't require running server)
    secrets_pass = test_secrets_requirement()

    # Start API server
    server_started = await start_api_server()

    if not server_started:
        print("\n❌ Cannot run API tests without server. Please start the API server manually:")
        print("   cd /Users/ericsingh/Desktop/Fora Travel/normalize-bot")
        print("   source venv/bin/activate")
        print("   python src/app.py")
        return

    # Run API tests
    latency_pass = await test_latency_requirement()
    stability_pass = await test_stability_requirement()
    errors_pass = await test_http_errors_requirement()

    # Summary
    print("\n" + "=" * 60)
    print("REQUIREMENTS TEST SUMMARY")
    print("=" * 60)

    results = [
        ("Latency p95 ≤ 20s", latency_pass),
        ("Stability < 1% non-2xx", stability_pass),
        ("Informative JSON errors", errors_pass),
        ("Secrets via env vars only", secrets_pass)
    ]

    all_passed = True
    for requirement, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{requirement:<25} {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL REQUIREMENTS PASSED!")
    else:
        print("❌ SOME REQUIREMENTS FAILED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())