import importlib
import os
import sys

import pytest

os.environ["USE_MOCK_DB"] = "true"
os.environ["ARDUINO_ENABLED"] = "false"
os.environ["FLASK_DEBUG"] = "false"


@pytest.fixture(scope="session")
def app_module():
    if "app" in sys.modules:
        module = importlib.reload(sys.modules["app"])
    else:
        module = importlib.import_module("app")

    return module


@pytest.fixture(autouse=True)
def reset_database(app_module):
    app_module.users.delete_many({})
    app_module.students.delete_many({})
    app_module.visitors.delete_many({})
    app_module.movement_logs.delete_many({})
    yield
    app_module.users.delete_many({})
    app_module.students.delete_many({})
    app_module.visitors.delete_many({})
    app_module.movement_logs.delete_many({})


@pytest.fixture
def app(app_module):
    app_module.app.config.update(TESTING=True)
    return app_module.app


@pytest.fixture
def client(app):
    return app.test_client()
