"""
Endpoint test script — tests all Railway API endpoints.
Run: .\venv\Scripts\python.exe test_endpoints.py
"""
import requests
import json
import time

BASE_URL = "https://communication-app-production-81aa.up.railway.app/api/v1"

# ─── Test credentials (uses a throwaway test account) ────────────────────────
TEST_EMAIL    = "endpointtest_99@test.com"
TEST_PASSWORD = "Test@1234"
TEST_NAME     = "Endpoint Tester"

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

results = []

def log(label, passed, status_code=None, body=None, error=None):
    icon = f"{GREEN}✅{RESET}" if passed else f"{RED}❌{RESET}"
    code = f"[{status_code}]" if status_code else ""
    print(f"{icon} {BOLD}{label}{RESET} {code}")
    if not passed and error:
        print(f"   {RED}Error: {error}{RESET}")
    if body and not passed:
        preview = str(body)[:200]
        print(f"   {YELLOW}Body: {preview}{RESET}")
    results.append((label, passed))

def section(title):
    print(f"\n{BOLD}{'─'*55}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'─'*55}{RESET}")

# ─────────────────────────────────────────────────────────────────────────────
section("1. AUTH ENDPOINTS")
# ─────────────────────────────────────────────────────────────────────────────

# 1a. Register
try:
    r = requests.post(f"{BASE_URL}/auth/register/", json={
        "name": TEST_NAME, "email": TEST_EMAIL, "password": TEST_PASSWORD
    }, timeout=15)
    # 201 = created, 400 = already exists (still means endpoint works)
    ok = r.status_code in (200, 201, 400)
    log("POST /auth/register/", ok, r.status_code, r.json() if not ok else None)
except Exception as e:
    log("POST /auth/register/", False, error=str(e))

time.sleep(0.5)

# 1b. Login
access_token = None
try:
    r = requests.post(f"{BASE_URL}/auth/login/", json={
        "email": TEST_EMAIL, "password": TEST_PASSWORD
    }, timeout=15)
    ok = r.status_code == 200
    body = r.json()
    if ok:
        access_token = body.get("access") or body.get("access_token") or body.get("tokens", {}).get("access")
    log("POST /auth/login/", ok, r.status_code, body if not ok else None)
    if ok and not access_token:
        print(f"   {YELLOW}⚠ Login OK but could not find access token in response: {list(body.keys())}{RESET}")
except Exception as e:
    log("POST /auth/login/", False, error=str(e))

time.sleep(0.5)

# 1c. Forgot password
try:
    r = requests.post(f"{BASE_URL}/auth/forgot-password/", json={
        "email": TEST_EMAIL
    }, timeout=15)
    ok = r.status_code in (200, 201)
    log("POST /auth/forgot-password/", ok, r.status_code, r.json() if not ok else None)
except Exception as e:
    log("POST /auth/forgot-password/", False, error=str(e))

time.sleep(0.5)

# ─────────────────────────────────────────────────────────────────────────────
section("2. USERS ENDPOINTS")
# ─────────────────────────────────────────────────────────────────────────────

auth_header = {"Authorization": f"Bearer {access_token}"} if access_token else {}

# 2a. Get profile
try:
    r = requests.get(f"{BASE_URL}/users/profile/", headers=auth_header, timeout=15)
    ok = r.status_code in (200, 201)
    log("GET /users/profile/", ok, r.status_code, r.json() if not ok else None)
    if not access_token:
        print(f"   {YELLOW}⚠ Skipped — no access token from login{RESET}")
except Exception as e:
    log("GET /users/profile/", False, error=str(e))

time.sleep(0.5)

# ─────────────────────────────────────────────────────────────────────────────
section("3. AI TEACHER ENDPOINTS")
# ─────────────────────────────────────────────────────────────────────────────

if not access_token:
    print(f"{YELLOW}⚠ Skipping AI Teacher tests — login failed, no access token.{RESET}")
else:
    # 3a. Evaluate text (Speaking practice)
    try:
        r = requests.post(f"{BASE_URL}/ai-teacher/evaluate/", json={
            "text": "i go to school now"
        }, headers=auth_header, timeout=30)
        body = r.json()
        ok = r.status_code == 200 and "corrected_text" in body and body.get("score_out_of_10", -1) >= 0
        log("POST /ai-teacher/evaluate/", ok, r.status_code, body if not ok else None)
        if ok:
            print(f"   Score: {body.get('score_out_of_10')}/10")
            print(f"   Feedback: {str(body.get('detailed_feedback',''))[:100]}")
    except Exception as e:
        log("POST /ai-teacher/evaluate/", False, error=str(e))

    time.sleep(1)

    # 3b. English correct (Grammar coach)
    try:
        r = requests.post(f"{BASE_URL}/ai-teacher/correct/", json={
            "text": "she go to market yesterday"
        }, headers=auth_header, timeout=30)
        body = r.json()
        ok = r.status_code == 200 and "corrected_text" in body
        log("POST /ai-teacher/correct/", ok, r.status_code, body if not ok else None)
        if ok:
            print(f"   Score: {body.get('score_out_of_10')}/10")
            print(f"   Corrected: {body.get('corrected_text','')[:100]}")
    except Exception as e:
        log("POST /ai-teacher/correct/", False, error=str(e))

    time.sleep(1)

    # 3c. Listening generate
    try:
        r = requests.post(f"{BASE_URL}/ai-teacher/listening/generate/", json={
            "difficulty": "medium"
        }, headers=auth_header, timeout=30)
        body = r.json()
        ok = r.status_code == 200 and "sentence" in body
        log("POST /ai-teacher/listening/generate/", ok, r.status_code, body if not ok else None)
        generated_sentence = body.get("sentence", "") if ok else ""
        if ok:
            print(f"   Sentence: {generated_sentence[:100]}")
    except Exception as e:
        log("POST /ai-teacher/listening/generate/", False, error=str(e))
        generated_sentence = ""

    time.sleep(1)

    # 3d. Listening evaluate
    try:
        sentence = generated_sentence or "The quick brown fox jumps over the lazy dog."
        r = requests.post(f"{BASE_URL}/ai-teacher/listening/evaluate/", json={
            "original_sentence": sentence,
            "user_response": "The quick brown fox jumped over the lazy dog."
        }, headers=auth_header, timeout=30)
        body = r.json()
        ok = r.status_code == 200 and "score_out_of_10" in body
        log("POST /ai-teacher/listening/evaluate/", ok, r.status_code, body if not ok else None)
        if ok:
            print(f"   Score: {body.get('score_out_of_10')}/10  |  Good: {body.get('is_good')}")
    except Exception as e:
        log("POST /ai-teacher/listening/evaluate/", False, error=str(e))

# ─────────────────────────────────────────────────────────────────────────────
section("4. GREETING SHORTCUT (no API billing)")
# ─────────────────────────────────────────────────────────────────────────────

if access_token:
    try:
        r = requests.post(f"{BASE_URL}/ai-teacher/evaluate/", json={
            "text": "hello"
        }, headers=auth_header, timeout=15)
        body = r.json()
        ok = r.status_code == 200 and body.get("score_out_of_10") == 10
        log("POST /ai-teacher/evaluate/ (greeting shortcut)", ok, r.status_code, body if not ok else None)
        if ok:
            print(f"   ✨ Greeting short-circuit working — no API cost")
    except Exception as e:
        log("POST /ai-teacher/evaluate/ (greeting shortcut)", False, error=str(e))

# ─────────────────────────────────────────────────────────────────────────────
section("SUMMARY")
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(1 for _, ok in results if ok)
total  = len(results)
print(f"\n  {GREEN if passed == total else YELLOW}{passed}/{total} tests passed{RESET}\n")
for label, ok in results:
    icon = f"{GREEN}✅{RESET}" if ok else f"{RED}❌{RESET}"
    print(f"  {icon} {label}")
print()
