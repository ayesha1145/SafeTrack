# ============================================================
# SafeTrack Translation Module
# ------------------------------------------------------------
# Replaces the old hardcoded English/Bengali-only dictionary with
# Azure Translator, so SafeTrack can serve ANY language Azure
# supports (100+) without adding new dictionaries by hand.
#
# Design notes:
# - Source-of-truth strings are defined once, in English, below.
# - Translations are fetched from Azure Translator on first request
#   for a given (key, language) pair, then cached in memory for the
#   life of the process — so repeat requests are instant and don't
#   re-hit the API or cost more quota.
# - Fails soft: if Azure isn't configured or a call errors, we fall
#   back to English rather than breaking the request. A missing
#   translation should never block a student from using the app.
# ============================================================

import os
import logging
import requests
import uuid

logger = logging.getLogger(__name__)

AZURE_TRANSLATOR_KEY = os.environ.get("AZURE_TRANSLATOR_KEY")
AZURE_TRANSLATOR_ENDPOINT = os.environ.get(
    "AZURE_TRANSLATOR_ENDPOINT", "https://api.cognitive.microsofttranslator.com"
)
AZURE_TRANSLATOR_REGION = os.environ.get("AZURE_TRANSLATOR_REGION", "eastus")

TRANSLATION_ENABLED = bool(AZURE_TRANSLATOR_KEY)

if not TRANSLATION_ENABLED:
    logger.warning(
        "AZURE_TRANSLATOR_KEY not set — dynamic translation is disabled. "
        "App will fall back to English (and cached Bengali strings) only."
    )

# Source-of-truth strings, in English. Adding a new key here makes it
# available in every supported language automatically.
BASE_STRINGS = {
    "welcome": "Welcome to SafeTrack",
    "emergency_alert": "Emergency Alert",
    "profile_updated": "Profile updated successfully",
    "alert_created": "Emergency alert created successfully",
    "invalid_credentials": "Invalid credentials",
    "user_exists": "User already exists",
    "user_registered": "User registered successfully",
    "alert_resolved": "Alert marked as resolved",
    "rate_limited": "Too many requests — please slow down",
}

# Pre-seeded so Bengali (the app's original second language) works
# instantly with zero API calls, and still works if Azure is ever down.
_cache = {
    ("welcome", "bn"): "SafeTrack এ স্বাগতম",
    ("emergency_alert", "bn"): "জরুরি সতর্কতা",
    ("profile_updated", "bn"): "প্রোফাইল সফলভাবে আপডেট হয়েছে",
    ("alert_created", "bn"): "জরুরি সতর্কতা সফলভাবে তৈরি হয়েছে",
    ("invalid_credentials", "bn"): "অবৈধ পরিচয়পত্র",
    ("user_exists", "bn"): "ব্যবহারকারী ইতিমধ্যে বিদ্যমান",
    ("user_registered", "bn"): "ব্যবহারকারী সফলভাবে নিবন্ধিত হয়েছে",
}


def _translate_via_azure(text: str, target_lang: str) -> str:
    """Call Azure Translator for a single string. Returns the original
    English text on any failure (soft-fail — never raises)."""
    if not TRANSLATION_ENABLED:
        return text

    try:
        url = f"{AZURE_TRANSLATOR_ENDPOINT}/translate"
        params = {"api-version": "3.0", "to": target_lang}
        headers = {
            "Ocp-Apim-Subscription-Key": AZURE_TRANSLATOR_KEY,
            "Ocp-Apim-Subscription-Region": AZURE_TRANSLATOR_REGION,
            "Content-type": "application/json",
            "X-ClientTraceId": str(uuid.uuid4()),
        }
        body = [{"text": text}]
        response = requests.post(url, params=params, headers=headers, json=body, timeout=5)
        response.raise_for_status()
        result = response.json()
        return result[0]["translations"][0]["text"]
    except Exception as e:
        logger.error(f"Azure Translator request failed for lang={target_lang}: {e}")
        return text


def get_translation(key: str, lang: str = "en") -> str:
    """Get a UI string in the requested language. Handles caching and
    falls back to English if the key or language isn't available."""
    base_text = BASE_STRINGS.get(key, key)

    if lang == "en" or not lang:
        return base_text

    cache_key = (key, lang)
    if cache_key in _cache:
        return _cache[cache_key]

    translated = _translate_via_azure(base_text, lang)
    _cache[cache_key] = translated
    return translated
