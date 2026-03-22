"""
pdf_trans_tools CLI - Command-line interface for PDF translation
"""
import argparse
import logging
import sys
from pathlib import Path

from pdf_trans_tools import Translator


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def translate_single(args: argparse.Namespace) -> int:
    """Translate a single PDF file."""
    translator = Translator(api_key=args.api_key, target_lang=args.target_lang)

    try:
        logging.info(f"Translating {args.input} to {args.target_lang}")
        result = translator.translate_pdf(args.input, args.output, args.target_lang)

        if result:
            logging.info(f"Successfully translated to {args.output}")
            return 0
        else:
            logging.error("Translation failed")
            return 1
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return 1


def translate_batch(args: argparse.Namespace) -> int:
    """Translate multiple PDF files in batch."""
    translator = Translator(api_key=args.api_key, target_lang=args.target_lang)

    input_path = Path(args.input)
    if input_path.is_file():
        files = [input_path]
    else:
        files = list(input_path.glob("*.pdf"))

    if not files:
        logging.error(f"No PDF files found in {args.input}")
        return 1

    logging.info(f"Found {len(files)} PDF files to translate")

    success_count = 0
    fail_count = 0

    for pdf_file in files:
        output_name = pdf_file.stem + f"_translated_{args.target_lang}" + ".pdf"
        output_path = Path(args.output) / output_name if args.output else output_name

        try:
            logging.info(f"Translating {pdf_file} -> {output_path}")
            result = translator.translate_pdf(str(pdf_file), str(output_path), args.target_lang)

            if result:
                success_count += 1
                logging.info(f"Success: {output_path}")
            else:
                fail_count += 1
                logging.error(f"Failed: {pdf_file}")
        except Exception as e:
            fail_count += 1
            logging.error(f"Error translating {pdf_file}: {e}")

    logging.info(f"Batch complete: {success_count} succeeded, {fail_count} failed")
    return 0 if fail_count == 0 else 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="pdf_trans_tools - PDF Translation Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--api-key", "-k",
        help="Google Translate API key",
        env_var="GOOGLE_TRANSLATE_API_KEY",
        default=None
    )

    parser.add_argument(
        "--target-lang", "-l",
        default="en",
        help="Target language code (default: en)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Single file translation
    single_parser = subparsers.add_parser("translate", help="Translate a single PDF file")
    single_parser.add_argument("input", help="Input PDF file path")
    single_parser.add_argument("output", help="Output PDF file path")

    # Batch translation
    batch_parser = subparsers.add_parser("batch", help="Translate multiple PDF files")
    batch_parser.add_argument("input", help="Input PDF file or directory path")
    batch_parser.add_argument("output", nargs="?", help="Output directory path (optional)")

    # Extract text command
    extract_parser = subparsers.add_parser("extract", help="Extract text from PDF")
    extract_parser.add_argument("input", help="Input PDF file path")
    extract_parser.add_argument("--output", "-o", help="Output text file path (optional)")

    args = parser.parse_args()

    setup_logging(args.verbose)

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "translate":
        return translate_single(args)
    elif args.command == "batch":
        return translate_batch(args)
    elif args.command == "extract":
        translator = Translator()
        try:
            text = translator.extract_text(args.input)
            if args.output:
                Path(args.output).write_text(text)
                logging.info(f"Text extracted to {args.output}")
            else:
                print(text)
            return 0
        except Exception as e:
            logging.error(f"Extraction error: {e}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
