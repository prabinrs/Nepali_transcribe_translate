# llm_service.py
import requests
import base64
import json
import os # To access environment variables

# --- Google Gemini API Client ---
# Using requests directly as Streamlit doesn't directly run Google Generative AI client
# with its own API Key management. The client is designed for server-side.
# We're passing the API key from Streamlit's secrets.

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

def transcribe_audio_gemini(audio_bytes: bytes, mime_type: str, gemini_api_key: str) -> str:
    """
    Transcribes audio bytes to Nepali text using Google Gemini's gemini-2.0-flash model.

    Args:
        audio_bytes (bytes): The raw bytes of the audio file.
        mime_type (str): The MIME type of the audio file (e.g., "audio/webm", "audio/mp3").
        gemini_api_key (str): Your Google Gemini API key.

    Returns:
        str: The transcribed Nepali text.

    Raises:
        Exception: If the API call fails or returns an unexpected response.
    """
    if not gemini_api_key:
        raise ValueError("Gemini API Key is missing for transcription.")

    headers = {
        "Content-Type": "application/json",
    }
    # Encode audio bytes to base64
    base64_audio_data = base64.b64encode(audio_bytes).decode('utf-8')

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": "Transcribe the following Nepali audio to text:"},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": base64_audio_data
                        }
                    }
                ]
            }
        ]
    }

    url = f"{GEMINI_API_BASE_URL}/gemini-2.0-flash:generateContent?key={gemini_api_key}"

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        result = response.json()

        if result.get("candidates") and len(result["candidates"]) > 0 and \
           result["candidates"][0].get("content") and \
           result["candidates"][0]["content"].get("parts") and \
           len(result["candidates"][0]["content"]["parts"]) > 0:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            raise Exception(f"Unexpected response structure from Gemini API: {result}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network or API error during Gemini transcription: {e}")
    except Exception as e:
        raise Exception(f"Failed to transcribe audio with Gemini: {e}")


def _call_ollama(base_url: str, model_name: str, prompt: str) -> str:
    """Helper to call Ollama API."""
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
    }
    try:
        response = requests.post(f"{base_url}/api/generate", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ollama API error: {e}")
    except Exception as e:
        raise Exception(f"Failed to get response from Ollama: {e}")


def _call_vllm(base_url: str, prompt: str) -> str:
    """Helper to call vLLM API (assuming OpenAI-compatible chat completions)."""
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "default", # Or a specific model name if your vLLM requires it
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 150,
    }
    try:
        response = requests.post(f"{base_url}/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if data.get("choices") and len(data["choices"]) > 0 and data["choices"][0].get("message"):
            return data["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Unexpected response structure from vLLM API: {data}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"vLLM API error: {e}")
    except Exception as e:
        raise Exception(f"Failed to get response from vLLM: {e}")


def _call_gemini_text(gemini_api_key: str, prompt: str) -> str:
    """Helper to call Gemini text generation API for translation."""
    if not gemini_api_key:
        raise ValueError("Gemini API Key is missing for translation.")

    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ]
    }
    url = f"{GEMINI_API_BASE_URL}/gemini-2.0-flash:generateContent?key={gemini_api_key}"

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        if result.get("candidates") and len(result["candidates"]) > 0 and \
           result["candidates"][0].get("content") and \
           result["candidates"][0]["content"].get("parts") and \
           len(result["candidates"][0]["content"]["parts"]) > 0:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            raise Exception(f"Unexpected response structure from Gemini API: {result}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network or API error during Gemini translation: {e}")
    except Exception as e:
        raise Exception(f"Failed to translate with Gemini: {e}")


def translate_text(
    text_to_translate: str,
    target_language: str,
    model_provider: str,
    gemini_api_key: str = None,
    ollama_base_url: str = None,
    ollama_model_name: str = None,
    vllm_base_url: str = None
) -> str:
    """
    Translates text using the specified LLM provider.

    Args:
        text_to_translate (str): The text to translate.
        target_language (str): The target language (e.g., "English").
        model_provider (str): The chosen LLM provider ("Gemini", "Ollama", "vLLM").
        gemini_api_key (str, optional): Gemini API key, if Gemini is the provider.
        ollama_base_url (str, optional): Base URL for Ollama, if Ollama is the provider.
        ollama_model_name (str, optional): Model name for Ollama.
        vllm_base_url (str, optional): Base URL for vLLM, if vLLM is the provider.

    Returns:
        str: The translated text.

    Raises:
        ValueError: If a required parameter for the chosen provider is missing.
        Exception: If the translation fails.
    """
    prompt = f"Translate the following Nepali text to {target_language}: \"{text_to_translate}\""

    if model_provider == "Gemini":
        if not gemini_api_key:
            raise ValueError("Gemini API key is required for Gemini translation.")
        return _call_gemini_text(gemini_api_key, prompt)
    elif model_provider == "Ollama":
        if not ollama_base_url or not ollama_model_name:
            raise ValueError("Ollama Base URL and Model Name are required for Ollama translation.")
        return _call_ollama(ollama_base_url, ollama_model_name, prompt)
    elif model_provider == "vLLM":
        if not vllm_base_url:
            raise ValueError("vLLM Base URL is required for vLLM translation.")
        return _call_vllm(vllm_base_url, prompt)
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")

