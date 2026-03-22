"""
pdf_trans_tools pdf_writer - PDF generation module
"""
import logging

from pdf_trans_tools.exceptions import PDFWriteError

logger = logging.getLogger(__name__)

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError:
    canvas = None


class PdfWriterHelper:
    """Handles PDF generation operations."""

    def __init__(self):
        if canvas is None:
            raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")

    def generate_pdf(self, text_content: str, output_path: str, title: str = "Document") -> bool:
        """
        Generate a PDF from text content.

        Args:
            text_content: The text to write to PDF
            output_path: Path where the output PDF should be saved
            title: Title for the document

        Returns:
            bool: True if PDF generation succeeded

        Raises:
            PDFWriteError: If PDF generation fails
        """
        try:
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter

            # Write title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, title)

            # Write content
            c.setFont("Helvetica", 10)
            y_position = height - 80

            lines = text_content.split('\n')
            for line in lines:
                # Wrap long lines
                if len(line) > 80:
                    words = line.split()
                    current_line = ""
                    for word in words:
                        if len(current_line) + len(word) + 1 <= 80:
                            current_line += (" " + word if current_line else word)
                        else:
                            c.drawString(50, y_position, current_line)
                            y_position -= 12
                            current_line = word
                            if y_position < 50:
                                c.showPage()
                                c.setFont("Helvetica", 10)
                                y_position = height - 50
                    if current_line:
                        c.drawString(50, y_position, current_line)
                        y_position -= 12
                else:
                    c.drawString(50, y_position, line)
                    y_position -= 12

                if y_position < 50:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y_position = height - 50

            c.save()
            logger.debug(f"PDF generated successfully: {output_path}")
            return True
        except Exception as e:
            raise PDFWriteError(f"Failed to generate PDF: {e}")
