"""
pdf_trans_tools web - Local web interface for PDF translation
"""
import os
import tempfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max upload

# Import translator components
from pdf_trans_tools import Translator

translator = Translator()


@app.route("/")
def index():
    """Render main page."""
    return render_template("index.html")


@app.route("/api/translate", methods=["POST"])
def translate():
    """
    Translate a PDF file.

    Expects:
        - file: PDF file upload
        - target_lang: Target language code
        - source_lang: Source language code (optional, auto-detect if empty)
        - validate: Whether to run validation (default: true)

    Returns:
        JSON with:
            - success: bool
            - output_path: Path to translated PDF (if successful)
            - validation_result: Validation details (if requested)
            - error: Error message (if failed)
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"})

    target_lang = request.form.get("target_lang", "zh")
    source_lang = request.form.get("source_lang", "")
    validate = request.form.get("validate", "true").lower() == "true"

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"success": False, "error": "File must be a PDF"})

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as input_tmp:
            file.save(input_tmp.name)
            input_path = input_tmp.name

        # Create output path
        output_path = input_path.replace(".pdf", f"_translated_{target_lang}.pdf")

        # Translate with or without validation
        if validate:
            success, validation_result = translator.translate_pdf_with_validation(
                input_path, output_path, target_lang
            )
            result = {
                "success": success,
                "output_path": output_path,
                "validation": {
                    "is_valid": validation_result.is_valid,
                    "message": validation_result.message,
                    "differences": validation_result.differences
                }
            }
        else:
            success = translator.translate_pdf(input_path, output_path, target_lang)
            result = {"success": success, "output_path": output_path}

        # Cleanup input file
        os.unlink(input_path)

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/extract", methods=["POST"])
def extract_text():
    """
    Extract text from a PDF file without translating.

    Expects:
        - file: PDF file upload

    Returns:
        JSON with:
            - success: bool
            - text: Extracted text content
            - page_count: Number of pages
            - error: Error message (if failed)
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"})

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"success": False, "error": "File must be a PDF"})

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as input_tmp:
            file.save(input_tmp.name)
            input_path = input_tmp.name

        # Extract text and info
        text = translator.extract_text(input_path)
        info = translator.get_pdf_info(input_path)

        # Cleanup
        os.unlink(input_path)

        return jsonify({
            "success": True,
            "text": text,
            "page_count": info.get("page_count", 0)
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/download/<path:filename>")
def download(filename):
    """Download a translated file."""
    return send_file(filename, as_attachment=True)


def run_server(host="127.0.0.1", port=5000, debug=True):
    """Run the web server."""
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server()
