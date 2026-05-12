"""Record a short scripted UI flow as docs/screenshots/demo.gif.

Run from the e2e container (after capture_screenshots.py seeded the demo project):

    docker compose -f docker-compose-dev.yml --profile e2e run --rm \\
        --entrypoint bash e2e -c \\
        "pip install -q playwright && playwright install chromium >/dev/null && \\
         apt-get update -qq && apt-get install -y -qq ffmpeg >/dev/null && \\
         python /tests/e2e/scripts/capture_demo_gif.py"
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

API_URL = os.environ.get("TESTJAM_API_URL", "http://api:8000/api/v1")
FRONTEND_URL = os.environ.get("TESTJAM_FRONTEND_URL", "http://frontend:5173")
ADMIN_USER = os.environ.get("TESTJAM_USER", "admin")
ADMIN_PASS = os.environ.get("TESTJAM_PASS", "admin123")

OUT_DIR = Path("/tests/e2e/screenshots-out")
GIF_WIDTH = 1000
GIF_FPS = 10
VIEWPORT = {"width": 1440, "height": 810}


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    token = _login()
    project_id, execution_id = _lookup_demo(token)

    video_dir = OUT_DIR / "_video"
    video_dir.mkdir(exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(
            viewport=VIEWPORT,
            device_scale_factor=1,
            record_video_dir=str(video_dir),
            record_video_size=VIEWPORT,
        )
        context.add_init_script(f"localStorage.setItem('token', {token!r});")
        page = context.new_page()

        _flow(page, project_id, execution_id)

        page.close()
        context.close()
        browser.close()

    webm = next(video_dir.glob("*.webm"))
    gif = OUT_DIR / "demo.gif"
    _to_gif(webm, gif)
    print(f"  ✓ demo.gif ({gif.stat().st_size // 1024} KB)")

    shutil.rmtree(video_dir, ignore_errors=True)


def _flow(page, project_id: int, execution_id: int) -> None:
    page.goto(f"{FRONTEND_URL}/projects", wait_until="networkidle")
    page.wait_for_selector("h1:has-text(\"Projects\")", timeout=10_000)
    page.wait_for_timeout(1_500)

    page.click("a:has-text(\"Demo Webshop\")")
    page.wait_for_selector("h1:has-text(\"Demo Webshop\")", timeout=10_000)
    page.wait_for_timeout(2_000)

    page.click("[role=\"treeitem\"][aria-label=\"Checkout\"]")
    page.wait_for_timeout(1_200)
    page.click("[role=\"treeitem\"][aria-label=\"Login & Auth\"]")
    page.wait_for_timeout(1_200)

    page.goto(f"{FRONTEND_URL}/projects/{project_id}/executions", wait_until="networkidle")
    page.wait_for_timeout(1_500)

    page.goto(f"{FRONTEND_URL}/executions/{execution_id}/run", wait_until="networkidle")
    page.wait_for_selector("h1", timeout=10_000)
    page.wait_for_timeout(2_000)

    for _ in range(3):
        page.keyboard.press("j")
        page.wait_for_timeout(700)

    page.keyboard.press("p")
    page.wait_for_timeout(1_000)
    page.keyboard.press("j")
    page.wait_for_timeout(600)
    page.keyboard.press("f")
    page.wait_for_timeout(1_500)


def _to_gif(webm: Path, gif: Path) -> None:
    palette = webm.parent / "palette.png"
    trim = "1.5"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-ss", trim, "-i", str(webm),
         "-vf", f"fps={GIF_FPS},scale={GIF_WIDTH}:-1:flags=lanczos,palettegen=stats_mode=diff",
         str(palette)],
        check=True,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-ss", trim, "-i", str(webm), "-i", str(palette),
         "-lavfi", f"fps={GIF_FPS},scale={GIF_WIDTH}:-1:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=5",
         str(gif)],
        check=True,
    )


def _login() -> str:
    resp = requests.post(
        f"{API_URL}/auth/login",
        data={"username": ADMIN_USER, "password": ADMIN_PASS},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _lookup_demo(token: str) -> tuple[int, int]:
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    projects = session.get(f"{API_URL}/projects").json()
    project = next((p for p in projects if p["name"] == "Demo Webshop"), None)
    if project is None:
        raise SystemExit("Demo Webshop project not found — run capture_screenshots.py first")
    execs = session.get(f"{API_URL}/projects/{project['id']}/executions").json()
    if not execs:
        raise SystemExit("No executions in Demo Webshop — run capture_screenshots.py first")
    return project["id"], execs[0]["id"]


if __name__ == "__main__":
    main()
