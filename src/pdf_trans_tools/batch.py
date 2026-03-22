"""
pdf_trans_tools batch - Batch processing with parallel execution
"""
import logging
import concurrent.futures
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result of a batch operation."""
    total: int
    succeeded: int
    failed: int
    results: list[tuple[str, bool, Optional[str]]]


class BatchProcessor:
    """Process multiple PDF translations in parallel."""

    def __init__(self, max_workers: int = 4):
        """
        Initialize batch processor.

        Args:
            max_workers: Maximum number of parallel workers
        """
        self.max_workers = max_workers
        self._completed = 0
        self._total = 0

    def translate_batch(
        self,
        translator: Callable,
        input_paths: list[str],
        output_dir: Optional[str] = None,
        target_lang: str = "en",
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> BatchResult:
        """
        Translate multiple PDF files in parallel.

        Args:
            translator: Translator instance or function to use for translation
            input_paths: List of input PDF file paths
            output_dir: Optional output directory for translated files
            target_lang: Target language code
            progress_callback: Optional callback(completed, total) for progress updates

        Returns:
            BatchResult with statistics and individual results
        """
        self._completed = 0
        self._total = len(input_paths)
        results = []

        def translate_one(input_path: str) -> tuple[str, bool, Optional[str]]:
            """Translate a single file."""
            try:
                input_p = Path(input_path)
                if output_dir:
                    output_path = Path(output_dir) / f"{input_p.stem}_translated_{target_lang}{input_p.suffix}"
                else:
                    output_path = f"{input_p.stem}_translated_{target_lang}{input_p.suffix}"

                # Use translator if it's a callable (function/method)
                if callable(translator):
                    success = translator(str(input_path), str(output_path), target_lang)
                else:
                    success = translator.translate_pdf(str(input_path), str(output_path), target_lang)

                self._completed += 1
                if progress_callback:
                    progress_callback(self._completed, self._total)

                return (str(input_path), success, None)
            except Exception as e:
                self._completed += 1
                if progress_callback:
                    progress_callback(self._completed, self._total)
                return (str(input_path), False, str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(translate_one, path) for path in input_paths]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        succeeded = sum(1 for _, success, _ in results if success)
        failed = len(results) - succeeded

        return BatchResult(
            total=len(results),
            succeeded=succeeded,
            failed=failed,
            results=results
        )
