# Edge Voice TTS

A small command-line tool that turns text into speech with the Microsoft Edge "Read aloud"
neural voices: 300+ voices in 100+ languages, with speed and pitch control. Works as a
`cli_wrapper` text-to-speech plugin (see `manifest.json`).

## Install in Pal Engine

1. Download `EdgeVoiceTTS-<version>.zip` from the
   [latest release](https://github.com/spasimirkirov/tts-edge-voice/releases/latest).
2. In Pal Engine, open **Settings › Integrations**, click **Add Zip**, choose the zip and click
   **Save**.
3. Choose **Edge TTS Provider** in **Settings › Voice › Default TTS Provider**, or for one character in
   Home › This character › Voice.

Updates: Pal Engine checks this repository for new releases. When one is out, **Settings ›
Integrations** shows an **Update** button next to the integration. Needs an internet connection.

## Usage

```
EdgeVoiceTTS.exe --voice en-US-AriaNeural --text "Hello world" --output hello.mp3
EdgeVoiceTTS.exe --voice bg-BG-KalinaNeural --text "Здравей" --output hi.mp3 --speed 0.9 --pitch -10
EdgeVoiceTTS.exe --list-voices
EdgeVoiceTTS.exe --export-voices-json voices.json
```

| Option | Meaning |
|---|---|
| `--voice` | Voice id from `--list-voices`, e.g. `en-US-AriaNeural` |
| `--text` / `--text-file` | Text to speak (UTF-8 file for `--text-file`) |
| `--output` | MP3 file to write |
| `--speed` | Speaking rate multiplier, 0.5 to 2 (default 1). A bare `--speed` means 1 |
| `--pitch` | Pitch offset in Hz, -50 to 50 (default 0). A bare `--pitch` means 0 |

Run from source: `pip install -r requirements.txt`, then `python main.py ...`.

## Pal Engine persistent worker (`--serve`)

Pal Engine 0.8.5+ starts the exe once with `--serve` and keeps it running, instead of one process per
sentence (`"serve": "--serve"` and `"persistent_worker": true` in `manifest.json`). One JSON object
per line:

```
<- {"event": "ready"}
-> {"id": "7", "action": "synthesize", "text": "Hello", "voice_id": "VOICE", "output": "C:\tmp\x.mp3", "speed": 1.0, "pitch": 0}
<- {"id": "7", "ok": true, "output": "C:\tmp\x.mp3"}
<- {"id": "7", "ok": false, "error": "..."}
```

Requests come on stdin, responses and the ready line go to stdout (logs to stderr), one request at
a time. The worker ends when stdin closes. Older Pal Engine versions ignore `serve` and keep using
the `generate` command.

## Voices catalog

`--export-voices-json` writes `voices.json` in categories, the way Pal Engine fills its voice slots:

```json
{ "categories": [
  { "category": "female",  "voices": [ { "id": "bg-BG-KalinaNeural", "name": "Kalina (bg-BG)", "locale": "bg-BG", "language": "Bulgarian (Bulgaria)", "gender": "female" } ] },
  { "category": "male",    "voices": [ ... ] },
  { "category": "neutral", "voices": [ every voice ] }
] }
```

Edge has only female and male voices, so `neutral` lists all of them. `language` ("English (United
Kingdom)") is what the host groups voices by; `locale` is the code (en-GB).

## Privacy and availability

This is an unofficial client. The text you convert is sent to Microsoft's speech service
(the endpoint the Edge browser uses for reading pages aloud). Microsoft can change or close
it at any time.

## Releases

Bump `version` in `manifest.json` and merge to `main`: the `Release` GitHub Actions workflow builds
the exe, takes the voices catalog from the live service, and publishes release `v<version>` with
the plugin zip. Pal Engine's integration updater (`update.github` in the manifest) offers it to
users. A merge without a version change builds nothing; pushing a matching tag by hand also
works. Build locally with `./build_exe.ps1`.

## License

MIT for the code in this repository (`LICENSE`).

The speech protocol is handled by [edge-tts](https://github.com/rany2/edge-tts), licensed
under the LGPL-3.0 (`LICENSE.edge-tts.txt`). The released exe bundles an unmodified copy of
it; to use a different version, change `requirements.txt` and rebuild from this source.
