import argparse
import sys
from pathlib import Path

from edge_voice import EdgeTTSError, list_voices, synthesize, voices_catalog
from edge_voice.client import dump_catalog, run

DEFAULT_SPEED = 1.0
DEFAULT_PITCH_HZ = 0.0


def _optional_float(default: float):
    """--speed / --pitch may come without a value: a host that does not fill the {speed}
    placeholder leaves the bare flag, which then means the default."""
    def parse(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            raise argparse.ArgumentTypeError(f"not a number: {value}")
    return {"nargs": "?", "type": parse, "const": default, "default": default}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate speech with the Microsoft Edge Read Aloud voices (unofficial).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-t", "--text", help="Text to speak.")
    group.add_argument("--text-file", type=Path, help="UTF-8 text file to speak.")
    group.add_argument("--list-voices", action="store_true", help="Print every voice id and exit.")
    group.add_argument("--export-voices-json", type=Path,
                       help="Write the voices catalog (id, name, locale, gender) as JSON and exit.")
    group.add_argument("--serve", action="store_true",
                       help="Run as Pal Engine's persistent worker: JSON requests on stdin, one per line.")

    parser.add_argument("-v", "--voice", default="en-US-AriaNeural", help="Voice id, e.g. en-US-AriaNeural.")
    parser.add_argument("-o", "--output", default="output.mp3", help="Output MP3 path.")
    parser.add_argument("--speed", help="Speaking rate multiplier, 0.5 to 2.", **_optional_float(DEFAULT_SPEED))
    parser.add_argument("--pitch", help="Pitch offset in Hz, -50 to 50.", **_optional_float(DEFAULT_PITCH_HZ))
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.serve:
        from edge_voice.serve import serve
        return serve()

    try:
        if args.list_voices:
            for voice in voices_catalog(run(list_voices())):
                print(voice["id"])
            return 0

        if args.export_voices_json:
            catalog = voices_catalog(run(list_voices()))
            args.export_voices_json.parent.mkdir(parents=True, exist_ok=True)
            args.export_voices_json.write_text(dump_catalog(catalog), encoding="utf-8")
            print(f"{len(catalog)} voices saved to {args.export_voices_json}")
            return 0

        if args.text is None and args.text_file is None:
            parser.error("one of --text or --text-file is required unless --list-voices, --export-voices-json or --serve is used")

        text = args.text if args.text is not None else args.text_file.read_text(encoding="utf-8")
        speed = min(2.0, max(0.5, args.speed))
        pitch = min(50.0, max(-50.0, args.pitch))
        audio = run(synthesize(text, args.voice, speed=speed, pitch_hz=pitch))
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(audio)
        print(f"Audio saved to {output}")
        return 0
    except (EdgeTTSError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except Exception as error:  # network and protocol errors from aiohttp
        print(f"error: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
