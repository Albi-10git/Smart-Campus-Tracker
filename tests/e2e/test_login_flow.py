import os
import threading
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from werkzeug.serving import make_server


class LiveServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=5001):
        super().__init__(daemon=True)
        self.server = make_server(host, port, app)
        self.context = app.app_context()
        self.context.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()
        self.context.pop()


@pytest.fixture
def live_server(app, app_module):
    app_module.users.insert_one({"username": "admin", "password": "admin123"})
    server = LiveServerThread(app)
    server.start()
    yield "http://127.0.0.1:5001"
    server.shutdown()


@pytest.fixture
def browser():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    chrome_binary = os.getenv("CHROME_BINARY_PATH")
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH")

    if chrome_binary:
        options.binary_location = chrome_binary

    try:
        if chromedriver_path and Path(chromedriver_path).exists():
            driver = webdriver.Chrome(
                service=Service(chromedriver_path),
                options=options
            )
        else:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
    except WebDriverException as exc:
        pytest.skip(f"Chrome WebDriver is unavailable: {exc}")

    yield driver
    driver.quit()


def test_login_flow_loads_dashboard(live_server, browser):
    browser.get(f"{live_server}/login")

    browser.find_element(By.ID, "username").send_keys("admin")
    browser.find_element(By.ID, "password").send_keys("admin123")
    browser.find_element(By.ID, "login-panel").submit()

    WebDriverWait(browser, 10).until(EC.url_contains("/dashboard"))
    assert "/dashboard" in browser.current_url
    assert "Movement Dashboard" in browser.page_source
