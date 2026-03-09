"""
Pure HTTP integration test for Marketing Product Report endpoints.
Tests: POST /reports, GET /reports, GET /reports/{id}, PATCH /reports/{id}/status
"""
import requests
import json
import sys

# Fix Unicode output on Windows
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

CUSTOMER1_EMAIL = "customer1@nexprime.com"
CUSTOMER2_EMAIL = "customer3@nexprime.com"
ADMIN_EMAIL = "admin@nexprime.com"
CUSTOMER_PASS = "password123"
ADMIN_PASS = "admin123"

def sep(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print('='*55)

def ok(label, condition, detail=""):
    icon = "[PASS]" if condition else "[FAIL]"
    msg = f"  {icon} {label}"
    if detail:
        msg += f" | {detail}"
    print(msg)
    return condition

def login(email, password):
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if resp.status_code == 200:
        data = resp.json()
        return data.get("access_token"), data.get("user", {}).get("id")
    print(f"  [FAIL] Login failed for {email}: {resp.status_code} {resp.text[:150]}")
    return None, None

def get_marketing_product_id(token):
    resp = requests.get(f"{BASE_URL}/marketing-products", headers={"Authorization": f"Bearer {token}"})
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]["id"]
    return None

def run_tests():
    passed = 0
    failed = 0

    sep("Step 1: Login")
    c1_token, c1_id = login(CUSTOMER1_EMAIL, CUSTOMER_PASS)
    c2_token, c2_id = login(CUSTOMER2_EMAIL, CUSTOMER_PASS)
    adm_token, adm_id = login(ADMIN_EMAIL, ADMIN_PASS)

    if ok("Customer1 login", c1_token is not None, f"ID={c1_id}"): passed += 1
    else: failed += 1
    if ok("Customer2 login", c2_token is not None, f"ID={c2_id}"): passed += 1
    else: failed += 1
    if ok("Admin login", adm_token is not None, f"ID={adm_id}"): passed += 1
    else: failed += 1

    if not (c1_token and c2_token and adm_token):
        print("\n[ABORT] Login failed - stopping tests.")
        return

    c1h = {"Authorization": f"Bearer {c1_token}"}
    adh = {"Authorization": f"Bearer {adm_token}"}

    mp_id = get_marketing_product_id(c1_token)
    if ok("MarketingProduct found", mp_id is not None, f"ID={mp_id}"): passed += 1
    else:
        failed += 1
        mp_id = 1

    # ---- TEST 1: POST /reports ------------------------------------------------
    sep("TEST 1: POST /reports")

    payload = {
        "reporterUserId": c1_id,
        "targetUserId": c2_id,
        "marketingProductId": mp_id,
        "content": "This marketing product is a scam. Price is inflated and product does not exist."
    }
    resp = requests.post(f"{BASE_URL}/reports", json=payload, headers=c1h)
    print(f"  HTTP {resp.status_code}")

    report_id = None
    if resp.status_code == 200:
        d = resp.json()
        report_id = d.get("id")
        if ok("Report created", True, f"ID={report_id}"): passed += 1
        if ok("status=PENDING", d.get("status") == "PENDING", d.get("status")): passed += 1
        else: failed += 1
        if ok("action=NONE", d.get("action") == "NONE", d.get("action")): passed += 1
        else: failed += 1
        if ok("reporter.email correct", d.get("reporter", {}).get("email") == CUSTOMER1_EMAIL,
               d.get("reporter", {}).get("email", "missing")): passed += 1
        else: failed += 1
        if ok("target.email correct", d.get("target", {}).get("email") == CUSTOMER2_EMAIL,
               d.get("target", {}).get("email", "missing")): passed += 1
        else: failed += 1
        if ok("marketingProduct present", "marketingProduct" in d,
               d.get("marketingProduct", {}).get("name", "missing")): passed += 1
        else: failed += 1
        print(f"\n  Response:\n{json.dumps(d, indent=4, ensure_ascii=True)}")
    else:
        failed += 1
        ok("Report creation FAILED", False, resp.text[:300])

    # ---- TEST 2: GET /reports -------------------------------------------------
    sep("TEST 2: GET /reports (Admin)")

    resp = requests.get(f"{BASE_URL}/reports", headers=adh)
    print(f"  HTTP {resp.status_code}")
    if resp.status_code == 200:
        d = resp.json()
        if ok("All reports loaded", True, f"count={len(d)}"): passed += 1
        if d:
            first = d[0]
            if ok("reporter field exists", "reporter" in first): passed += 1
            else: failed += 1
            if ok("target field exists", "target" in first): passed += 1
            else: failed += 1
            if ok("marketingProduct field exists", "marketingProduct" in first): passed += 1
            else: failed += 1
    else:
        failed += 1
        ok("GET /reports FAILED", False, resp.text[:300])

    # ---- TEST 3: GET /reports/{id} --------------------------------------------
    sep(f"TEST 3: GET /reports/{report_id}")

    if report_id:
        resp = requests.get(f"{BASE_URL}/reports/{report_id}", headers=adh)
        print(f"  HTTP {resp.status_code}")
        if resp.status_code == 200:
            d = resp.json()
            if ok("Single report loaded", d.get("id") == report_id, f"ID={d.get('id')}"): passed += 1
            else: failed += 1
            if ok("reporter.email", d.get("reporter", {}).get("email") == CUSTOMER1_EMAIL,
                   d.get("reporter", {}).get("email")): passed += 1
            else: failed += 1
            if ok("target.email", d.get("target", {}).get("email") == CUSTOMER2_EMAIL,
                   d.get("target", {}).get("email")): passed += 1
            else: failed += 1
        else:
            failed += 1
            ok("GET /reports/{id} FAILED", False, resp.text[:300])
    else:
        print("  [SKIP] No report_id available")

    # ---- TEST 4a: DISMISSED ---------------------------------------------------
    sep("TEST 4a: PATCH /reports/{id}/status -> DISMISSED")

    # Create a fresh report for DISMISS test
    r2 = requests.post(f"{BASE_URL}/reports", json={
        "reporterUserId": c1_id, "targetUserId": c2_id,
        "marketingProductId": mp_id,
        "content": "Dismiss test report."
    }, headers=c1h)
    dismiss_id = r2.json().get("id") if r2.status_code == 200 else None
    ok("Created report for dismiss test", dismiss_id is not None, f"ID={dismiss_id}")

    if dismiss_id:
        resp = requests.patch(f"{BASE_URL}/reports/{dismiss_id}/status",
                              json={"status": "DISMISSED"}, headers=adh)
        print(f"  HTTP {resp.status_code}")
        if ok("DISMISSED response 200", resp.status_code == 200, resp.json().get("detail", "")): 
            passed += 1
        else: failed += 1

        verify = requests.get(f"{BASE_URL}/reports/{dismiss_id}", headers=adh)
        if ok("Report deleted after DISMISS (404)", verify.status_code == 404,
               f"status={verify.status_code}"): passed += 1
        else: failed += 1

    # ---- TEST 4b: REVIEWED ----------------------------------------------------
    sep(f"TEST 4b: PATCH /reports/{report_id}/status -> REVIEWED")

    if report_id:
        resp = requests.patch(f"{BASE_URL}/reports/{report_id}/status",
                              json={"status": "REVIEWED"}, headers=adh)
        print(f"  HTTP {resp.status_code}")
        if resp.status_code == 200:
            d = resp.json()
            if ok("REVIEWED response 200", True): passed += 1
            if isinstance(d, dict) and "status" in d:
                if ok("status=REVIEWED", d.get("status") == "REVIEWED", d.get("status")): passed += 1
                else: failed += 1
                if ok("action=ACCOUNT_INACTIVE", d.get("action") == "ACCOUNT_INACTIVE", d.get("action")): passed += 1
                else: failed += 1
            # Verify target account is INACTIVE via login attempt
            login_check = requests.post(f"{BASE_URL}/auth/login",
                                        json={"email": CUSTOMER2_EMAIL, "password": CUSTOMER_PASS})
            if ok("Target user now INACTIVE (login blocked)", login_check.status_code != 200,
                   f"login_status={login_check.status_code}"): passed += 1
            else: failed += 1
            print(f"\n  Response:\n{json.dumps(d, indent=4, ensure_ascii=True)}")
        else:
            failed += 1
            ok("REVIEWED FAILED", False, resp.text[:400])

    # ---- Summary --------------------------------------------------------------
    sep("SUMMARY")
    total = passed + failed
    print(f"  PASSED : {passed}/{total}")
    print(f"  FAILED : {failed}/{total}")
    if failed == 0:
        print("  [SUCCESS] All tests passed!")
    else:
        print("  [WARNING] Some tests failed - see above.")

if __name__ == "__main__":
    run_tests()
