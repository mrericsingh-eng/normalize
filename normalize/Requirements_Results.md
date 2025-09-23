NORMALIZE-BOT API REQUIREMENTS TESTING                                   
     ============================================================

     ============================================================
     TESTING SECRETS REQUIREMENT (Only via environment variables)
     ============================================================
     ✅ OPENAI_API_KEY found in environment (starts with: sk-proj-***...)

     Scanning 9 source files for hardcoded secrets...
     ✅ .env file found for development configuration
     ✅ PASS: No hardcoded secrets found, using environment variables properly
     Starting API server...
     ✅ API server is already running
     ============================================================
     TESTING LATENCY REQUIREMENT (p95 ≤ 20s)
     ============================================================
     Request 1/50: 3.99s (Status: 200)
     Request 2/50: 4.26s (Status: 200)
     Request 3/50: 3.25s (Status: 200)
     Request 4/50: 3.16s (Status: 200)
     Request 5/50: 5.83s (Status: 200)
     Request 6/50: 4.82s (Status: 200)
     Request 7/50: 3.57s (Status: 200)
     Request 8/50: 4.19s (Status: 200)
     Request 9/50: 4.58s (Status: 200)
     Request 10/50: 3.20s (Status: 200)
     Request 11/50: 3.27s (Status: 200)
     Request 12/50: 5.43s (Status: 200)
     Request 13/50: 4.19s (Status: 200)
     Request 14/50: 3.57s (Status: 200)
     Request 15/50: 4.52s (Status: 200)
     Request 16/50: 4.33s (Status: 200)
     Request 17/50: 2.85s (Status: 200)
     Request 18/50: 3.59s (Status: 200)
     Request 19/50: 5.29s (Status: 200)
     Request 20/50: 4.36s (Status: 200)
     Request 21/50: 3.04s (Status: 200)
     Request 22/50: 4.49s (Status: 200)
     Request 23/50: 4.40s (Status: 200)
     Request 24/50: 3.06s (Status: 200)
     Request 25/50: 3.03s (Status: 200)
     Request 26/50: 5.40s (Status: 200)
     Request 27/50: 4.30s (Status: 200)
     Request 28/50: 3.45s (Status: 200)
     Request 29/50: 3.94s (Status: 200)
     Request 30/50: 4.58s (Status: 200)
     Request 31/50: 2.71s (Status: 200)
     Request 32/50: 3.44s (Status: 200)
     Request 33/50: 5.28s (Status: 200)
     Request 34/50: 3.97s (Status: 200)
     Request 35/50: 3.00s (Status: 200)
     Request 36/50: 4.01s (Status: 200)
     Request 37/50: 4.22s (Status: 200)
     Request 38/50: 2.83s (Status: 200)
     Request 39/50: 2.99s (Status: 200)
     Request 40/50: 6.27s (Status: 200)
     Request 41/50: 4.29s (Status: 200)
     Request 42/50: 3.49s (Status: 200)
     Request 43/50: 4.26s (Status: 200)
     Request 44/50: 4.24s (Status: 200)
     Request 45/50: 3.32s (Status: 200)
     Request 46/50: 2.97s (Status: 200)
     Request 47/50: 4.81s (Status: 200)
     Request 48/50: 3.97s (Status: 200)
     Request 49/50: 2.88s (Status: 200)
     Request 50/50: 4.19s (Status: 200)

     LATENCY RESULTS:
       Requests completed: 50
       Successful responses: 50
       Average latency: 3.98s
       Min latency: 2.71s
       Max latency: 6.27s
       P95 latency: 5.61s
       Threshold: 20.0s
       ✅ PASS: P95 latency (5.61s) ≤ 20.0s

     ============================================================
     TESTING STABILITY REQUIREMENT (200 requests, < 1% non-2xx)
     ============================================================
     Progress: 10/200 requests completed - Success rate: 100.0%
     Progress: 20/200 requests completed - Success rate: 100.0%
     Progress: 30/200 requests completed - Success rate: 100.0%
     Progress: 40/200 requests completed - Success rate: 100.0%
     Progress: 50/200 requests completed - Success rate: 100.0%
     Progress: 60/200 requests completed - Success rate: 100.0%
     Progress: 70/200 requests completed - Success rate: 100.0%
     Progress: 80/200 requests completed - Success rate: 100.0%
     Progress: 90/200 requests completed - Success rate: 100.0%
     Progress: 100/200 requests completed - Success rate: 100.0%
     Progress: 110/200 requests completed - Success rate: 100.0%
     Progress: 120/200 requests completed - Success rate: 100.0%
     Progress: 130/200 requests completed - Success rate: 100.0%
     Progress: 140/200 requests completed - Success rate: 100.0%
     Progress: 150/200 requests completed - Success rate: 100.0%
     Progress: 160/200 requests completed - Success rate: 100.0%
     Progress: 170/200 requests completed - Success rate: 100.0%
     Progress: 180/200 requests completed - Success rate: 100.0%
     Progress: 190/200 requests completed - Success rate: 100.0%
     Progress: 200/200 requests completed - Success rate: 100.0%

     STABILITY RESULTS:
       Total requests: 200
       Successful (2xx): 200
       Non-2xx/Errors: 0
       Success rate: 100.0%
       Error rate: 0.0%
       Status code breakdown: {200: 200}
       ✅ PASS: Error rate (0.0%) < 1%

     ============================================================
     TESTING HTTP ERRORS REQUIREMENT (Informative JSON bodies)
     ============================================================

     Test 1: Invalid JSON body
       Status Code: 422
       Response body: {
       "detail": [
         {
           "type": "json_invalid",
           "loc": [
             "body",
     0
           ],
           "msg": "JSON decode error",
           "input": {},
           "ctx": {
             "error": "Expecting value"
           }
         }
       ]
     }
       ✅ PASS: Informative JSON error body

     Test 2: Missing required field
       Status Code: 422
       Response body: {
       "detail": [
         {
           "type": "missing",
           "loc": [
             "body",
     "text"
           ],
           "msg": "Field required",
           "input": {
             "message_id": "test-error-1"
           }
         }
       ]
     }
       ✅ PASS: Informative JSON error body

     Test 3: Invalid data types
       Status Code: 422
       Response body: {
       "detail": [
         {
           "type": "string_type",
           "loc": [
             "body",
     "message_id"
           ],
           "msg": "Input should be a valid string",
           "input": 123
         },
         {
           "type": "string_type",
           "loc": [
             "body",
     "text"
           ],
           "msg": "Input should be a valid string",
           "input": [
             "not",
             "a",
     "string"
           ]
         }
       ]
     }
       ✅ PASS: Informative JSON error body

       ✅ PASS: All HTTP errors have informative JSON bodies

     ============================================================
     REQUIREMENTS TEST SUMMARY
     ============================================================
     Latency p95 ≤ 20s         ✅ PASS
     Stability < 1% non-2xx    ✅ PASS
     Informative JSON errors   ✅ PASS
     Secrets via env vars only ✅ PASS
