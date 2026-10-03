"""
ZEROTrace Advisor — Acceptance Criteria Validator
Run: python validate_advisor.py

Tests all acceptance criteria from GitHub issue #1 without needing
a running server. Uses httpx ASGI transport to call the FastAPI app
in-process.
"""

import asyncio
import sys
import json
from pathlib import Path

# ── path setup ────────────────────────────────────────────────────────────────
_backend = Path(__file__).resolve().parent
for p in [str(_backend), str(_backend / "app")]:
    if p not in sys.path:
        sys.path.insert(0, p)

import httpx
from tests.test_app import test_app as app  # Minimal advisor-only test app


# ── ANSI colours ──────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

PASS = f"{GREEN}✔ PASS{RESET}"
FAIL = f"{RED}✗ FAIL{RESET}"

results: list[dict] = []


def record(name: str, passed: bool, detail: str = ""):
    status = PASS if passed else FAIL
    print(f"  {status}  {name}")
    if detail:
        print(f"         {YELLOW}{detail}{RESET}")
    results.append({"name": name, "passed": passed, "detail": detail})


# ══════════════════════════════════════════════════════════════════════════════
async def run_tests():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:

        # ── Section 1: HTTP 200 + valid JSON schemas ──────────────────────────
        print(f"\n{BOLD}{CYAN}━━━ AC-1: Endpoints respond with HTTP 200 + typed JSON ━━━{RESET}")

        # --- recommend: SSD DELETED ---
        r = await client.post("/api/v1/advisor/recommend", json={
            "storage_medium": "SSD",
            "file_system": "NTFS",
            "loss_scenario": "DELETED",
        })
        record("POST /api/v1/advisor/recommend → HTTP 200", r.status_code == 200,
               f"status={r.status_code}")

        body = r.json()
        required_keys = {"recommended_method", "risk_level", "safety_warnings", "action_type"}
        missing = required_keys - body.keys()
        record("Response has all required fields (AdvisorResponse schema)",
               len(missing) == 0, f"missing={missing or 'none'}")

        valid_risks   = {"LOW", "MEDIUM", "CRITICAL"}
        valid_actions = {"LAUNCH_CARVE", "IMAGE_DISK", "RUN_MFT_SCAN"}
        record("risk_level is valid enum value",
               body.get("risk_level") in valid_risks,
               f"got='{body.get('risk_level')}'")
        record("action_type is valid enum value",
               body.get("action_type") in valid_actions,
               f"got='{body.get('action_type')}'")
        record("safety_warnings is a list",
               isinstance(body.get("safety_warnings"), list),
               f"type={type(body.get('safety_warnings')).__name__}")

        # --- chat ---
        r2 = await client.post("/api/v1/advisor/chat", json={
            "question": "What is the best way to recover a deleted file?",
        })
        record("POST /api/v1/advisor/chat → HTTP 200", r2.status_code == 200,
               f"status={r2.status_code}")

        chat_body = r2.json()
        chat_keys = {"answer", "related_warnings", "suggested_action"}
        missing_chat = chat_keys - chat_body.keys()
        record("Chat response has all required fields (AdvisorChatResponse schema)",
               len(missing_chat) == 0, f"missing={missing_chat or 'none'}")

        # ── Section 2: SSD TRIM warnings ─────────────────────────────────────
        print(f"\n{BOLD}{CYAN}━━━ AC-2a: SSD + Deletion → TRIM safety warnings ━━━{RESET}")

        r = await client.post("/api/v1/advisor/recommend", json={
            "storage_medium": "SSD",
            "file_system": "EXFAT",
            "loss_scenario": "DELETED",
        })
        b = r.json()
        record("HTTP 200 for SSD DELETED", r.status_code == 200)
        record("risk_level == MEDIUM for SSD deletion",
               b["risk_level"] == "MEDIUM", f"got='{b['risk_level']}'")
        record("action_type == IMAGE_DISK (acquire before TRIM runs)",
               b["action_type"] == "IMAGE_DISK", f"got='{b['action_type']}'")

        trim_warn = any("TRIM" in w for w in b["safety_warnings"])
        record("Safety warnings contain TRIM keyword",
               trim_warn, f"warnings={b['safety_warnings']}")

        power_warn = any("power" in w.lower() for w in b["safety_warnings"])
        record("Safety warnings tell operator NOT to power on the SSD",
               power_warn, f"warnings={b['safety_warnings']}")

        # ── Section 2b: Mechanical / hardware failure ─────────────────────────
        print(f"\n{BOLD}{CYAN}━━━ AC-2b: HDD Hardware failure → CRITICAL + no direct carving ━━━{RESET}")

        r = await client.post("/api/v1/advisor/recommend", json={
            "storage_medium": "HDD",
            "file_system": "NTFS",
            "loss_scenario": "HARDWARE_ISSUE",
        })
        b = r.json()
        record("HTTP 200 for HDD HARDWARE_ISSUE", r.status_code == 200)
        record("risk_level == CRITICAL for mechanical failure",
               b["risk_level"] == "CRITICAL", f"got='{b['risk_level']}'")
        record("action_type == IMAGE_DISK",
               b["action_type"] == "IMAGE_DISK", f"got='{b['action_type']}'")

        no_carve_warn = any(
            "carv" in w.lower() or "direct" in w.lower()
            for w in b["safety_warnings"]
        )
        record("Safety warnings forbid direct software carving on failing drive",
               no_carve_warn, f"warnings={b['safety_warnings']}")

        click_warn = any("click" in w.lower() or "head" in w.lower() or "platter" in w.lower()
                         for w in b["safety_warnings"])
        record("Safety warnings mention read-head / platter damage (HDD-specific)",
               click_warn, f"warnings={b['safety_warnings']}")

        # ── Section 2c: Quick format → LOW risk ───────────────────────────────
        print(f"\n{BOLD}{CYAN}━━━ AC-2c: Quick Format → LOW risk + carving ━━━{RESET}")

        r = await client.post("/api/v1/advisor/recommend", json={
            "storage_medium": "USB",
            "file_system": "FAT32",
            "loss_scenario": "FORMATTED",
        })
        b = r.json()
        record("HTTP 200 for FORMATTED",  r.status_code == 200)
        record("risk_level == LOW",       b["risk_level"] == "LOW", f"got='{b['risk_level']}'")
        record("action_type == LAUNCH_CARVE",
               b["action_type"] == "LAUNCH_CARVE", f"got='{b['action_type']}'")

        # ── Section 2d: Fragmented MP4 ────────────────────────────────────────
        print(f"\n{BOLD}{CYAN}━━━ AC-2d: Fragmented MP4 → Fragment Graph recommendation ━━━{RESET}")

        r = await client.post("/api/v1/advisor/recommend", json={
            "storage_medium": "SSD",
            "file_system": "EXFAT",
            "loss_scenario": "DELETED",
            "target_extension": "mp4",
        })
        b = r.json()
        record("HTTP 200 for MP4 recovery", r.status_code == 200)
        record("action_type == LAUNCH_CARVE",
               b["action_type"] == "LAUNCH_CARVE", f"got='{b['action_type']}'")
        record("recommended_method mentions Fragment Graph",
               "Fragment" in b["recommended_method"],
               f"method='{b['recommended_method'][:80]}...'")

        # ── Section 2e: NTFS MFT scan ─────────────────────────────────────────
        print(f"\n{BOLD}{CYAN}━━━ AC-2e: NTFS Deletion → MFT scan ━━━{RESET}")

        r = await client.post("/api/v1/advisor/recommend", json={
            "storage_medium": "HDD",
            "file_system": "NTFS",
            "loss_scenario": "DELETED",
        })
        b = r.json()
        record("HTTP 200 for NTFS DELETED", r.status_code == 200)
        record("action_type == RUN_MFT_SCAN",
               b["action_type"] == "RUN_MFT_SCAN", f"got='{b['action_type']}'")

        # ── Section 3: Swagger / OpenAPI ──────────────────────────────────────
        print(f"\n{BOLD}{CYAN}━━━ AC-3: Swagger /docs & OpenAPI schema ━━━{RESET}")

        r = await client.get("/openapi.json")
        record("GET /openapi.json → HTTP 200", r.status_code == 200)

        spec = r.json()
        paths = spec.get("paths", {})
        record("/api/v1/advisor/recommend in OpenAPI spec",
               "/api/v1/advisor/recommend" in paths,
               f"paths_count={len(paths)}")
        record("/api/v1/advisor/chat in OpenAPI spec",
               "/api/v1/advisor/chat" in paths)

        # Verify schemas are registered
        components = spec.get("components", {}).get("schemas", {})
        record("AdvisorRequest schema registered in components",
               "AdvisorRequest" in components, f"schemas={list(components.keys())[:8]}")
        record("AdvisorResponse schema registered in components",
               "AdvisorResponse" in components)
        record("AdvisorChatRequest schema registered in components",
               "AdvisorChatRequest" in components)
        record("AdvisorChatResponse schema registered in components",
               "AdvisorChatResponse" in components)

        # ── Section 4: Validation error on bad input ──────────────────────────
        print(f"\n{BOLD}{CYAN}━━━ AC-4: 422 Validation error for bad input ━━━{RESET}")

        r = await client.post("/api/v1/advisor/recommend", json={
            "storage_medium": "FLOPPY",   # invalid enum
            "file_system": "NTFS",
            "loss_scenario": "DELETED",
        })
        record("Invalid storage_medium → HTTP 422",
               r.status_code == 422, f"status={r.status_code}")

        r = await client.post("/api/v1/advisor/chat", json={
            "question": "ab",             # too short (min_length=3)
        })
        record("Too-short chat question → HTTP 422",
               r.status_code == 422, f"status={r.status_code}")

        # ── Section 5: Chat TRIM Q&A ──────────────────────────────────────────
        print(f"\n{BOLD}{CYAN}━━━ AC-5: Chat endpoint forensic Q&A ━━━{RESET}")

        r = await client.post("/api/v1/advisor/chat", json={
            "question": "Is it safe to run carving on an SSD with TRIM enabled?",
        })
        b = r.json()
        record("Chat TRIM question → HTTP 200", r.status_code == 200)
        record("Chat TRIM answer is non-empty", len(b.get("answer", "")) > 20)
        record("Chat TRIM returns safety warnings",
               len(b.get("related_warnings", [])) > 0,
               f"warnings={b.get('related_warnings', [])}")
        record("Chat TRIM suggests IMAGE_DISK action",
               b.get("suggested_action") == "IMAGE_DISK",
               f"suggested={b.get('suggested_action')}")

        r = await client.post("/api/v1/advisor/chat", json={
            "question": "My HDD is making a clicking sound and failing with bad sectors",
        })
        b = r.json()
        record("Chat mechanical failure → HTTP 200", r.status_code == 200)
        record("Chat mechanical returns critical warnings",
               len(b.get("related_warnings", [])) >= 2,
               f"warnings_count={len(b.get('related_warnings', []))}")


# ══════════════════════════════════════════════════════════════════════════════
def main():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  ZEROTrace Advisor — Acceptance Criteria Validation{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    asyncio.run(run_tests())

    total  = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"  Results: {GREEN}{passed}{RESET}/{total} passed  |  {RED}{failed}{RESET} failed")
    print(f"{BOLD}{'='*60}{RESET}\n")

    if failed:
        print(f"{RED}FAILED TESTS:{RESET}")
        for r in results:
            if not r["passed"]:
                print(f"  • {r['name']}")
                if r["detail"]:
                    print(f"    → {r['detail']}")
        sys.exit(1)
    else:
        print(f"{GREEN}{BOLD}✔ All acceptance criteria PASSED!{RESET}")


if __name__ == "__main__":
    main()
