import json
from openai import OpenAI

from .prompts import SYSTEM_PROMPT, GENERIC_PROMPT
from .schema import validate_and_enforce_schema


def extract_key_values(api_key: str, model: str, document_text: str, enforce_schema: bool = True) -> dict:
    client = OpenAI(api_key=api_key)
    
    # Choose prompt based on schema enforcement
    prompt = SYSTEM_PROMPT if enforce_schema else GENERIC_PROMPT

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": document_text},
        ],
        text={"format": {"type": "json_object"}},
    )

    result = json.loads(response.output_text)
    
    # Enforce the fixed schema only if requested
    if enforce_schema:
        result = validate_and_enforce_schema(result)
    
    return result