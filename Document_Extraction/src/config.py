import os
from dotenv import load_dotenv

load_dotenv()


def get_openai_settings():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4.1").strip()

    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY. Create a .env file.")

    return api_key, model