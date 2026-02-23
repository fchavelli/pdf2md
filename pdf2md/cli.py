"""Command-line interface for pdf2md."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from pdf2md import __version__
from pdf2md.ocr import process_pdf


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf2md",
        description="Convert PDF files to Markdown using Mistral OCR.",
    )
    parser.add_argument(
        "input",
        type=str,
        help="Path to the input PDF file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Path for the output Markdown file (default: <input>.md).",
    )
    parser.add_argument(
        "-i",
        "--images",
        action="store_true",
        default=False,
        help="Include images extracted from the PDF (saved alongside the .md file).",
    )
    parser.add_argument(
        "-k",
        "--api-key",
        type=str,
        default=None,
        help="Mistral API key (overrides MISTRAL_API_KEY env var / .env).",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help="Path to a .env file (default: searches in CWD and package dir).",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Load .env -----------------------------------------------------------
    if args.env_file:
        load_dotenv(args.env_file)
    else:
        # Try CWD first, then the package installation directory
        if not load_dotenv(Path.cwd() / ".env"):
            pkg_env = Path(__file__).resolve().parent.parent / ".env"
            load_dotenv(pkg_env)

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.is_file():
        print(f"Error: file not found – {input_path}", file=sys.stderr)
        sys.exit(1)

    if input_path.suffix.lower() != ".pdf":
        print("Warning: input file does not have a .pdf extension.", file=sys.stderr)

    mode_label = "with images" if args.images else "text-only"
    print(f"Processing {input_path.name} ({mode_label}) …")

    try:
        result = process_pdf(
            input_path,
            include_images=args.images,
            output_path=args.output,
            api_key=args.api_key,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Done → {result}")


if __name__ == "__main__":
    main()
