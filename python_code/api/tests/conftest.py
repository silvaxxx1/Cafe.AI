"""
Shared test configuration.

Sets required env vars at import time (before any agent __init__ runs)
so every test can construct agents without a real API key or .env file.
"""
import os

os.environ.setdefault("RUNPOD_TOKEN", "test-key")
os.environ.setdefault("RUNPOD_CHATBOT_URL", "http://fake-url/v1")
os.environ.setdefault("MODEL_NAME", "test-model")
