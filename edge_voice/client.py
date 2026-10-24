"""Thin wrapper around the edge-tts library (LGPL-3.0, https://github.com/rany2/edge-tts),
which speaks the Microsoft Edge "Read aloud" protocol.

Unofficial: the endpoint is the one the Edge browser uses to read pages aloud. Microsoft can
change it at any time; when that happens, updating edge-tts is usually the whole fix.
"""

import asyncio
import json
import re
from typing import Dict, List

import edge_tts


class EdgeTTSError(Exception):
    pass


def _rate(speed: float) -> str:
    return f"{round((speed - 1.0) * 100):+d}%"


def _pitch(pitch_hz: float) -> str:
    return f"{round(pitch_hz):+d}Hz"


def _clean_text(text: str) -> str:
    # Control characters break the SSML; line breaks become spaces.
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


async def synthesize(text: str, voice: str, speed: float = 1.0, pitch_hz: float = 0.0) -> bytes:
    """MP3 audio for the whole text (edge-tts splits long text itself)."""
    cleaned = _clean_text(text)
    if not cleaned:
        raise EdgeTTSError("text must not be empty")

    communicate = edge_tts.Communicate(cleaned, voice, rate=_rate(speed), pitch=_pitch(pitch_hz))
    audio = bytearray()
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio":
            audio.extend(chunk["data"])
    if not audio:
        raise EdgeTTSError(f"no audio received for voice {voice}")
    return bytes(audio)


async def list_voices() -> List[Dict[str, str]]:
    voices = await edge_tts.list_voices()
    return voices if isinstance(voices, list) else []


def run(coroutine):
    return asyncio.run(coroutine)


def voices_catalog(voices: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """One entry per voice: id (ShortName), name, locale, language, gender."""
    catalog = []
    for voice in voices:
        short_name = str(voice.get("ShortName") or "").strip()
        if not short_name:
            continue
        locale = str(voice.get("Locale") or "").strip()
        friendly = str(voice.get("FriendlyName") or "")
        # "Microsoft Aria Online (Natural) - English (United States)" -> "Aria"
        match = re.match(r"^Microsoft\s+(.+?)\s+Online", friendly)
        display = match.group(1) if match else short_name.rsplit("-", 1)[-1].replace("Neural", "")
        # "... - Bulgarian (Bulgaria)" -> "Bulgarian (Bulgaria)": the language and region the host
        # groups voices by. The locale code (bg-BG) when the name has no such part.
        language = friendly.rsplit(" - ", 1)[-1].strip() if " - " in friendly else locale
        catalog.append({
            "id": short_name,
            "name": f"{display} ({locale})" if locale else display,
            "locale": locale,
            "language": language,
            "gender": str(voice.get("Gender") or "").strip().lower(),
        })
    catalog.sort(key=lambda entry: (entry["locale"], entry["name"]))
    return catalog


# The categories Pal Engine fills its voice slots from. Edge has only female and male voices;
# "neutral" (for characters with a neutral gender) offers every voice.
CATEGORIES = ("female", "male", "neutral")


def categorized_catalog(catalog: List[Dict[str, str]]) -> Dict[str, list]:
    """voices.json for the host: {"categories": [{"category": ..., "voices": [...]}, ...]}."""
    return {
        "categories": [
            {
                "category": category,
                "voices": catalog if category == "neutral" else [v for v in catalog if v["gender"] == category],
            }
            for category in CATEGORIES
        ]
    }


def dump_catalog(catalog: List[Dict[str, str]]) -> str:
    return json.dumps(categorized_catalog(catalog), indent=2, ensure_ascii=False)
