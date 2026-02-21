import json
from openai import OpenAI

from .prompts import SYSTEM_PROMPT


def extract_key_values(api_key: str, model: str, document_text: str) -> dict:
    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": document_text},
        ],
        text={"format": {"type": "json_object"}},
    )

    return json.loads(response.output_text)