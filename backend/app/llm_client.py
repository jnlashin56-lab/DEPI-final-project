import os
import logging
from typing import Any, Dict
from huggingface_hub import InferenceClient
from json_repair import repair_json
import json
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"

def get_hf_token() -> str:
    token = os.getenv("HF_TOKEN")
    if not token:
        logger.warning("HF_TOKEN environment variable not set. Using free public endpoints, which may be rate-limited.")
    return token or ""

def get_client(model: str = DEFAULT_MODEL) -> InferenceClient:
    return InferenceClient(model=model, token=get_hf_token())

def generate_text(prompt: str, model: str = DEFAULT_MODEL, max_new_tokens: int = 500, temperature: float = 0.7) -> str:
    """Generates standard text from the LLM."""
    client = get_client(model)
    try:
        messages = [{"role": "user", "content": prompt}]
        response = client.chat_completion(
            messages=messages,
            max_tokens=max_new_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error in generate_text: {e}")
        raise

def generate_json(prompt: str, model: str = DEFAULT_MODEL, max_new_tokens: int = 500, temperature: float = 0.2) -> Dict[str, Any]:
    """Generates a JSON response and parses it robustly using json-repair."""
    client = get_client(model)
    try:
        # We enforce JSON output in the prompt
        full_prompt = f"{prompt}\n\nIMPORTANT: Respond ONLY with valid JSON. Do not include markdown formatting or explanations."
        messages = [{"role": "user", "content": full_prompt}]
        
        response = client.chat_completion(
            messages=messages,
            max_tokens=max_new_tokens,
            temperature=temperature,
        )
        content = response.choices[0].message.content.strip()
        
        # Use json_repair to handle common malformed JSON issues (e.g. trailing commas, missing brackets)
        repaired_json = repair_json(content, return_objects=True)
        
        if isinstance(repaired_json, dict):
             return repaired_json
        elif isinstance(repaired_json, list) and len(repaired_json) > 0:
             # Some prompts might return an array
             return {"data": repaired_json}
        else:
            # Fallback if parsing completely fails
            logger.error(f"Failed to parse repaired JSON into a dictionary. Repaired content: {repaired_json}")
            return {"error": "Failed to parse JSON response"}
            
    except Exception as e:
        logger.error(f"Error in generate_json: {e}")
        raise
