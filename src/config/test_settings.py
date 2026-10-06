import os

from src.config.settings import *  # noqa: F401,F403

SECRET_KEY = "test-secret-key-0123456789abcdef0123456789abcdef0123"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

os.environ.setdefault(
    "MODEL_ARTIFACT_PATH",
    os.path.join(
        os.path.dirname(__file__),
        "..", "..", "..", "BUSINESS LOGIC", "forecast-models", "theta_period7.pkl",
    ),
)
