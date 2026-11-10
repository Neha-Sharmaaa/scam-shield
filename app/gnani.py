"""Thin client for Gnani Prisma (STT) and Timbre (TTS).

Endpoints/params follow https://docs.gnani.ai (checked Nov 2026):
  STT  POST https://api.vachana.ai/stt/v3             multipart, header X-API-Key-ID
  TTS  POST https://api.vachana.ai/api/v1/tts/inference JSON,     header X-API-Key-ID

The API key is read from the environment (.env) and is never logged or returned.
All calls are serialized with a lock (some accounts allow 1 active request) and
retried with backoff on 429. Every TTS result is cached on disk by content hash
to save credits.
"""
import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

STT_URL = "https://api.vachana.ai/stt/v3"
TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"
STT_MODEL = "prisma-v3.0"
TTS_MODEL = "timbre-v3.0"
TTS_CACHE = ROOT / "data" / "tts_cache"

# Timbre v3.0 voices speak all 10 languages.
AGENT_VOICE = "Shivani"   # warm, patient female voice for the assistant
CALLER_VOICE = "Avinash"  # used only by the synthetic test-call generator

_lock = asyncio.Lock()

# Public-demo guard: a daily ceiling on real Gnani API requests (cached TTS doesn't count).
DAILY_CAP = int(os.environ.get("GNANI_DAILY_CAP", "400"))
_usage = {"day": None, "count": 0}


def usage() -> dict:
    return {"day": _usage["day"], "requests": _usage["count"], "daily_cap": DAILY_CAP}


class GnaniError(Exception):
    pass


def _key() -> str:
    key = os.environ.get("GNANI_API_KEY", "").strip()
    if not key:
        raise GnaniError("GNANI_API_KEY is not set (put it in .env)")
    return key


def has_key() -> bool:
    return bool(os.environ.get("GNANI_API_KEY", "").strip())


async def _post(**kwargs) -> httpx.Response:
    import datetime
    today = datetime.date.today().isoformat()
    if _usage["day"] != today:
        _usage.update(day=today, count=0)
    if _usage["count"] >= DAILY_CAP:
        raise GnaniError("The public demo has reached today's limit. Please try again tomorrow.")
    _usage["count"] += 1
    headers = kwargs.pop("headers", {})
    headers["X-API-Key-ID"] = _key()
    async with _lock:
        async with httpx.AsyncClient(timeout=60) as client:
            for attempt in range(5):
                r = await client.post(headers=headers, **kwargs)
                if r.status_code != 429:
                    return r
                await asyncio.sleep(0.6 * (attempt + 1))
            return r


def _err(r: httpx.Response) -> str:
    # Return the server's message only; never echo request headers.
    try:
        return f"HTTP {r.status_code}: {json.dumps(r.json(), ensure_ascii=False)[:300]}"
    except Exception:
        return f"HTTP {r.status_code}"


async def transcribe(wav_bytes: bytes, languages: str = "hi-IN,en-IN",
                     fmt: str = "codemix", keyterms: Optional[list] = None) -> dict:
    """Send an 8 kHz mono WAV clip (<=30 s) to Prisma v3.0. Returns the JSON body."""
    data = {
        "model": STT_MODEL,
        "language_code": languages,
        "format": fmt,
        "topic": "Phone call answered by a household assistant; caller states name, organisation and purpose.",
    }
    if keyterms:
        data["keyterms"] = json.dumps(keyterms, ensure_ascii=False)
    r = await _post(url=STT_URL, files={"audio_file": ("call.wav", wav_bytes, "audio/wav")}, data=data)
    if r.status_code != 200:
        raise GnaniError("Prisma " + _err(r))
    return r.json()


def _tts_cache_path(text: str, language: str, voice: str, sample_rate: int) -> Path:
    h = hashlib.sha256(f"{TTS_MODEL}|{voice}|{language}|{sample_rate}|{text}".encode()).hexdigest()[:24]
    return TTS_CACHE / f"{h}.wav"


async def synthesize(text: str, language: str = "hi-IN", voice: str = AGENT_VOICE,
                     sample_rate: int = 16000, speed: float = 0.95) -> Path:
    """Timbre v3.0 TTS -> WAV file path (cached by content hash)."""
    path = _tts_cache_path(text, language, voice, sample_rate)
    if path.exists() and path.stat().st_size > 100:
        return path
    payload = {
        "text": text,
        "voice": voice,
        "model": TTS_MODEL,
        "language": language,
        "speed": speed,
        "audio_config": {"sample_rate": sample_rate, "num_channels": 1, "sample_width": 2,
                         "encoding": "linear_pcm", "container": "wav"},
    }
    r = await _post(url=TTS_URL, json=payload, headers={"Content-Type": "application/json"})
    if r.status_code != 200 or not r.content:
        raise GnaniError("Timbre " + _err(r))
    TTS_CACHE.mkdir(parents=True, exist_ok=True)
    path.write_bytes(r.content)
    return path
