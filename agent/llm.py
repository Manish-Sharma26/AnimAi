import os
from typing import List

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please create a .env file with your API key.")

client = genai.Client(api_key=GEMINI_API_KEY)

# Prefer highest quality first, then faster/cheaper fallbacks.
PREFERRED_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-pro")
MODEL_PREFERENCE_ORDER = [
    PREFERRED_MODEL,
    "gemini-3.1-pro",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]


def _normalize_model_name(name: str) -> str:
    if not name:
        return ""
    return name.replace("models/", "")


def _discover_generate_content_models() -> List[str]:
    """
    Discover models accessible by this API key and keep only Gemini models
    that support generateContent.
    """
    discovered: List[str] = []
    try:
        for model in client.models.list():
            model_name = _normalize_model_name(getattr(model, "name", ""))
            if not model_name.startswith("gemini"):
                continue

            supported = getattr(model, "supported_actions", None) or []
            if supported and "generateContent" not in supported:
                continue

            discovered.append(model_name)
    except Exception:
        # If listing fails (network/API limitations), fallback to known names.
        return list(dict.fromkeys(MODEL_PREFERENCE_ORDER))

    if not discovered:
        return list(dict.fromkeys(MODEL_PREFERENCE_ORDER))

    return list(dict.fromkeys(discovered))


def _build_model_candidates() -> List[str]:
    """Order candidates by preference but keep only discovered models when possible."""
    available = _discover_generate_content_models()
    available_set = set(available)

    ordered: List[str] = []

    # Always try the user-configured preferred model first, even if discovery
    # does not report it (some projects expose preview aliases only).
    preferred_normalized = _normalize_model_name(PREFERRED_MODEL)
    if preferred_normalized:
        ordered.append(preferred_normalized)

    # If user asks for 3.1-pro, also try known 3.1 pro aliases before fallbacks.
    if preferred_normalized == "gemini-3.1-pro":
        for alias in ["gemini-3.1-pro-preview", "gemini-3.1-pro-preview-customtools"]:
            if alias not in ordered:
                ordered.append(alias)

    for model_name in MODEL_PREFERENCE_ORDER:
        normalized = _normalize_model_name(model_name)
        if normalized in available_set and normalized not in ordered:
            ordered.append(normalized)

    # Add any remaining discovered Gemini models at the end.
    for model_name in available:
        if model_name not in ordered:
            ordered.append(model_name)

    return ordered or list(dict.fromkeys(MODEL_PREFERENCE_ORDER))


def call_llm(prompt: str, max_tokens: int = 3000) -> str:
    """
    Sends a prompt to Gemini via google-genai and returns plain text.
    """
    last_error = None
    candidates = _build_model_candidates()

    for model_name in candidates:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.2,
                ),
            )
            text = getattr(response, "text", None)
            if text:
                return text
            return str(response)
        except Exception as err:
            last_error = err
            continue

    raise RuntimeError(
        "Gemini request failed for all configured/discovered models. "
        "Check your API key, model access, and quota/billing in Google AI Studio. "
        f"Tried: {candidates}. Last error: {last_error}"
    )