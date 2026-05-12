"""Generate marketing screenshots into /tests/e2e/screenshots-out/.

Run from the e2e container:

    docker compose -f docker-compose-dev.yml --profile e2e run --rm \\
        --entrypoint bash e2e -c \\
        "pip install -q playwright && playwright install chromium >/dev/null && \\
         python /tests/e2e/scripts/capture_screenshots.py"

The host receives the PNGs under tests/e2e/screenshots-out/ (bind-mounted).
"""

from __future__ import annotations

import os
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

API_URL = os.environ.get("TESTJAM_API_URL", "http://api:8000/api/v1")
FRONTEND_URL = os.environ.get("TESTJAM_FRONTEND_URL", "http://frontend:5173")
ADMIN_USER = os.environ.get("TESTJAM_USER", "admin")
ADMIN_PASS = os.environ.get("TESTJAM_PASS", "admin123")

OUT_DIR = Path("/tests/e2e/screenshots-out")
VIEWPORT = {"width": 1440, "height": 900}


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    token = _login()
    project_id, execution_id = _seed_demo(token)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(viewport=VIEWPORT, device_scale_factor=2)
        context.add_init_script(
            f"localStorage.setItem('token', {token!r});",
        )
        page = context.new_page()

        _shoot(page, f"{FRONTEND_URL}/projects", "h1:has-text(\"Projects\")", "hero.png")
        _shoot(page, f"{FRONTEND_URL}/projects/{project_id}", "h1:has-text(\"Demo Webshop\")", "suites.png")
        _shoot(page, f"{FRONTEND_URL}/executions/{execution_id}/run", "h1", "run.png")

        report_file = OUT_DIR / "_report.html"
        report = requests.get(
            f"{API_URL}/executions/{execution_id}/export/html",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
        report.raise_for_status()
        report_file.write_text(report.text)
        _shoot(page, f"file://{report_file}", "body", "report.png")
        report_file.unlink(missing_ok=True)

        browser.close()

    print(f"Saved screenshots to {OUT_DIR}")


def _login() -> str:
    resp = requests.post(
        f"{API_URL}/auth/login",
        data={"username": ADMIN_USER, "password": ADMIN_PASS},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _seed_demo(token: str) -> tuple[int, int]:
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"

    project = _ensure_project(session, "Demo Webshop")
    project_id = project["id"]

    suites = _ensure_suites(session, project_id, [
        ("Checkout", ["Add item to cart", "Apply coupon", "Pay with credit card", "Receive confirmation email"]),
        ("Login & Auth", ["Sign up new user", "Login with valid password", "Login with wrong password", "Reset password"]),
        ("Search & Catalog", ["Search by keyword", "Filter by category", "Sort by price"]),
    ])

    case_ids = [case_id for _, case_ids in suites.values() for case_id in case_ids]
    execution_id = _ensure_execution(session, project_id, case_ids)
    _mark_results(session, execution_id)
    return project_id, execution_id


def _ensure_project(session: requests.Session, name: str) -> dict:
    existing = session.get(f"{API_URL}/projects").json()
    for project in existing:
        if project["name"] == name:
            session.delete(f"{API_URL}/projects/{project['id']}")
            break
    resp = session.post(f"{API_URL}/projects", json={"name": name, "description": "Demo storefront with checkout, auth and catalog test suites."})
    resp.raise_for_status()
    return resp.json()


def _ensure_suites(
    session: requests.Session, project_id: int, blueprint: list[tuple[str, list[str]]],
) -> dict[str, tuple[int, list[int]]]:
    suites: dict[str, tuple[int, list[int]]] = {}
    for suite_name, case_names in blueprint:
        suite = session.post(
            f"{API_URL}/projects/{project_id}/suites",
            json={"name": suite_name},
        )
        suite.raise_for_status()
        suite_id = suite.json()["id"]
        case_ids = []
        for case_name in case_names:
            case = session.post(
                f"{API_URL}/suites/{suite_id}/cases",
                json={"name": case_name, "suite_id": suite_id},
            )
            case.raise_for_status()
            case_ids.append(case.json()["id"])
        suites[suite_name] = (suite_id, case_ids)
    return suites


def _ensure_execution(session: requests.Session, project_id: int, case_ids: list[int]) -> int:
    resp = session.post(
        f"{API_URL}/projects/{project_id}/executions",
        json={
            "title": "Sprint 24 regression",
            "type": "manual",
            "version": "1.4.0",
            "environment": "staging",
            "test_case_ids": case_ids,
        },
    )
    resp.raise_for_status()
    return resp.json()["id"]


def _mark_results(session: requests.Session, execution_id: int) -> None:
    results = session.get(f"{API_URL}/executions/{execution_id}/results").json()
    statuses = ["passed", "passed", "passed", "passed", "passed", "passed", "failed", "passed", "blocked", "passed"]
    for result, status in zip(results, statuses):
        session.put(
            f"{API_URL}/results/{result['id']}",
            json={"status": status},
        )


def _shoot(page, url: str, ready_selector: str, filename: str) -> None:
    page.goto(url, wait_until="networkidle")
    page.wait_for_selector(ready_selector, state="visible", timeout=10_000)
    page.wait_for_timeout(800)
    target = OUT_DIR / filename
    page.screenshot(path=str(target), full_page=False)
    print(f"  ✓ {filename}")


if __name__ == "__main__":
    main()
