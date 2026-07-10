import os
import logging
from typing import Any, Dict
import requests
from json_repair import repair_json
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

import time

# Azure OpenAI Configuration
AZURE_ENDPOINT = "https://yi30405251603817-3079-resource.services.ai.azure.com"
AZURE_DEPLOYMENT = "gpt-5-mini"
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_API_VERSION = "2025-04-01-preview"
DEFAULT_MODEL = AZURE_DEPLOYMENT

def _call_azure_api(prompt: str, model: str, max_tokens: int, temperature: float, retries: int = 3) -> str:
    url = f"{AZURE_ENDPOINT}/openai/deployments/{AZURE_DEPLOYMENT}/chat/completions?api-version={AZURE_API_VERSION}"
    headers = {
        "api-key": AZURE_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [{"role": "user", "content": prompt}],
    }
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code != 200:
                logger.error(f"Azure API error response: {response.status_code} - {response.text}")
            response.raise_for_status()
            data = response.json()
            logger.info(f"Azure API raw response keys: {list(data.keys())}")
            choice = data["choices"][0]
            message = choice["message"]
            logger.info(f"Azure API message keys: {list(message.keys())}")
            content = message.get("content") or ""
            logger.info(f"Azure API content (first 200 chars): {content[:200]}")
            return content.strip()
        except (requests.exceptions.HTTPError, requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            logger.warning(f"Azure API attempt {attempt}/{retries} failed: {e}")
            if attempt == retries:
                raise
            time.sleep(2 * attempt)

def generate_text(prompt: str, model: str = DEFAULT_MODEL, max_new_tokens: int = 500, temperature: float = 0.7) -> str:
    """Generates standard text from the LLM."""
    try:
        return _call_azure_api(prompt, model, max_new_tokens, temperature)
    except Exception as e:
        logger.error(f"Error in generate_text: {e}")
        raise

def generate_json(prompt: str, model: str = DEFAULT_MODEL, max_new_tokens: int = 500, temperature: float = 0.2) -> Dict[str, Any]:
    """Generates a JSON response and parses it robustly using json-repair."""
    try:
        # We enforce JSON output in the prompt
        full_prompt = f"{prompt}\n\nIMPORTANT: Respond ONLY with valid JSON. Do not include markdown formatting or explanations."
        logger.info(f"generate_json prompt length: {len(full_prompt)} characters")
        logger.debug(f"generate_json prompt:\n{full_prompt}")
        
        content = _call_azure_api(full_prompt, model, max_new_tokens, temperature)
        logger.info(f"generate_json raw content returned from LLM:\n{content}")
        
        # Use json_repair to handle common malformed JSON issues
        repaired_json = repair_json(content, return_objects=True)
        
        if isinstance(repaired_json, dict):
             return repaired_json
        elif isinstance(repaired_json, list):
             return {"data": repaired_json}
        else:
            logger.error(f"Failed to parse repaired JSON into a dictionary. Repaired content: {repaired_json}")
            return {"error": "Failed to parse JSON response"}
            
    except Exception as e:
        logger.error(f"Error in generate_json: {e}")
        raise

