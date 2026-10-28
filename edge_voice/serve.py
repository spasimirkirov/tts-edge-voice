"""`--serve`: Pal Engine's persistent TTS worker (protocol v1).

The host starts `EdgeVoiceTTS.exe --serve` once and keeps it running, instead of starting the exe
for every sentence (unpacking the one-file exe and importing Python each time costs 0.5-3 s).

    ready:     {"event": "ready"}                                   (stdout, once)
    request:   {"id": "7", "action": "synthesize", "text": "...", "voice_id": "en-US-AriaNeural",
                "output": "C:\\...\\x.mp3", "speed": 1.0, "pitch": 0}   (stdin, one per line)
    response:  {"id": "7", "ok": true, "output": "C:\\...\\x.mp3"}
               {"id": "7", "ok": false, "error": "..."}            (stdout, one per line)

One request at a time. Logs go to stderr, never stdout. The worker ends when stdin closes (the
host quit or stopped it).
"""

import asyncio
import json
import sys
from pathlib import Path

from .client import synthesize

DEFAULT_VOICE = "en-US-AriaNeural"


def _send(message: dict) -> None:
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _number(value, default: float, low: float, high: float) -> float:
    try:
        return min(high, max(low, float(value)))
    except (TypeError, ValueError):
        return default


def handle(request: dict, loop: asyncio.AbstractEventLoop) -> dict:
    """One request -> one response (never raises)."""
    request_id = request.get("id")
    try:
        if request.get("action", "synthesize") != "synthesize":
            raise ValueError(f"unknown action: {request.get('action')}")
        output = Path(str(request.get("output") or ""))
        if not str(output):
            raise ValueError("output is required")
        audio = loop.run_until_complete(synthesize(
            str(request.get("text") or ""),
            str(request.get("voice_id") or DEFAULT_VOICE),
            speed=_number(request.get("speed"), 1.0, 0.5, 2.0),
            pitch_hz=_number(request.get("pitch"), 0.0, -50.0, 50.0),
        ))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(audio)
        return {"id": request_id, "ok": True, "output": str(output)}
    except Exception as error:  # network, protocol and file errors
        return {"id": request_id, "ok": False, "error": f"{type(error).__name__}: {error}"}


def serve() -> int:
    # The host writes UTF-8 JSON; the Windows console default would break non-ASCII text.
    # utf-8-sig: a byte-order mark in front of the first line (PowerShell pipes add one) is skipped.
    sys.stdin.reconfigure(encoding="utf-8-sig")
    sys.stdout.reconfigure(encoding="utf-8")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _send({"event": "ready"})
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except ValueError:
                print(f"serve: not JSON: {line[:80]}", file=sys.stderr)
                continue
            if isinstance(request, dict):
                _send(handle(request, loop))
    finally:
        loop.close()
    return 0
