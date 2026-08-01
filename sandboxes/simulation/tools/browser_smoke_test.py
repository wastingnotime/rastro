"""Smoke-test the supervised Observatory through a real Chromium browser."""

from __future__ import annotations

import os
import subprocess
import time
from contextlib import closing
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


HOST = "127.0.0.1"
PORT = int(os.environ.get("MRL_BROWSER_SMOKE_PORT", "8876"))
BASE_URL = f"http://{HOST}:{PORT}"


def wait_for_server() -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            with closing(urlopen(f"{BASE_URL}/", timeout=1)):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("MRL supervision server did not start")


def main() -> None:
    environment = os.environ.copy()
    runtime_path = "/home/henrique/.wnt/runtime/mrl"
    source_path = os.path.abspath("sandboxes/simulation/src")
    environment["PYTHONPATH"] = f"{source_path}:{runtime_path}"
    server = subprocess.Popen(
        [
            "mrl-simulation",
            "supervise",
            "--scenario-factory",
            "app.simulation.mrl_runtime_scenario:create_simulation",
            "--host",
            HOST,
            "--port",
            str(PORT),
        ],
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        wait_for_server()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-gpu"],
            )
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.goto(BASE_URL, wait_until="domcontentloaded")
            page.locator("#run-state").wait_for()
            page.wait_for_function(
                "document.querySelector('#run-state').textContent.includes('paused')",
                timeout=15000,
            )

            page.locator('[data-inspection-tab="events"]').click()
            if "No domain events recorded yet." not in page.locator("#event-source").inner_text():
                raise AssertionError("reset state contains stale domain events")

            page.locator("#pace-select").select_option("1")
            page.locator('[data-command="resume"]').click()
            page.wait_for_timeout(1000)
            if "No domain events recorded yet." not in page.locator("#event-source").inner_text():
                raise AssertionError("delayed owner flow emitted an event too early")
            page.wait_for_function(
                "document.querySelector('#event-source').textContent.includes('warning_thresholds_customized')",
                timeout=20000,
            )

            timeline = page.request.get(f"{BASE_URL}/timeline").json()["observations"]
            if not any(
                observation["type"] == "domain_event"
                and observation["name"] == "warning_thresholds_customized"
                for observation in timeline
            ):
                raise AssertionError("timeline contains no event for the rendered flow")
            graph = page.request.get(f"{BASE_URL}/graph").json()["graph"]
            if not graph.get("nodes") or not graph.get("edges"):
                raise AssertionError("observatory graph metadata is empty")
            if not page.locator("#observatory-canvas").is_visible():
                raise AssertionError("observatory canvas is not visible")
            page.wait_for_function(
                "window.__mrlObservatoryDebug && window.__mrlObservatoryDebug.activeBeamNames().includes('CustomizeWarningThresholds')",
                timeout=10000,
            )
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)

    print("validated browser smoke: paused reset, delayed Play event, canvas, and graph")


if __name__ == "__main__":
    main()
