# Edge Voice TTS

A small command-line tool that turns text into speech with the Microsoft Edge "Read aloud"
neural voices: 300+ voices in 100+ languages, with speed and pitch control. Works as a
`cli_wrapper` text-to-speech plugin (see `manifest.json`).

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

## Privacy and availability

This is an unofficial client. The text you convert is sent to Microsoft's speech service
(the endpoint the Edge browser uses for reading pages aloud). Microsoft can change or close
it at any time.

## Releases

Push a tag that matches `version` in `manifest.json` (for example `v1.0.0`) and the
`Release` GitHub Actions workflow builds the exe, takes the voices catalog from the live
service, and attaches the plugin zip to a new release. Build locally with `./build_exe.ps1`.

## License

MIT for the code in this repository (`LICENSE`).

The speech protocol is handled by [edge-tts](https://github.com/rany2/edge-tts), licensed
under the LGPL-3.0 (`LICENSE.edge-tts.txt`). The released exe bundles an unmodified copy of
it; to use a different version, change `requirements.txt` and rebuild from this source.
