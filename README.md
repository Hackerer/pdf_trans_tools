# pdf_trans_tools

PDF translation tools for converting PDF documents between languages.

## Features

- PDF text extraction
- Translation integration
- Multi-format output support

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from pdf_trans_tools import Translator

translator = Translator()
translator.translate_pdf("input.pdf", "output.pdf", target_lang="en")
```

## Development

Run tests:
```bash
pytest tests/
```

## License

MIT
