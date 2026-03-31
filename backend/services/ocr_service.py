"""
OCR Service: Extract text from PDF/image CVs.
Supports PyMuPDF (fast, no ML) and EasyOCR (for scanned docs).
"""
import logging
import io
import re
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# ─── PyMuPDF (fitz) ───────────────────────────────────────────────────────────
try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
    logger.info("PyMuPDF available")
except ImportError:
    FITZ_AVAILABLE = False
    logger.warning("PyMuPDF not installed – PDF text extraction disabled")

# ─── EasyOCR ──────────────────────────────────────────────────────────────────
try:
    import easyocr
    EASYOCR_AVAILABLE = True
    logger.info("EasyOCR available")
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR not installed – OCR disabled")

# ─── pdfplumber fallback ───────────────────────────────────────────────────────
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

# ─── pypdf fallback ───────────────────────────────────────────────────────────
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


class OCRService:
    """Multi-strategy OCR/text-extraction service for CV files."""

    _easyocr_reader = None

    @classmethod
    def _get_easyocr_reader(cls):
        if cls._easyocr_reader is None and EASYOCR_AVAILABLE:
            logger.info("Initializing EasyOCR reader (first-time, may download model)...")
            cls._easyocr_reader = easyocr.Reader(["en", "fr"], gpu=False)
        return cls._easyocr_reader

    def extract_text(self, file_path: str) -> Tuple[str, float]:
        """
        Extract text from a PDF or image file.

        Returns:
            (text, confidence) where confidence is 0.0–1.0
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            return self._extract_from_pdf(file_path)
        elif suffix in (".png", ".jpg", ".jpeg", ".tiff", ".bmp"):
            return self._extract_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def extract_text_from_bytes(self, content: bytes, mime_type: str) -> Tuple[str, float]:
        """Extract text from raw bytes (for API upload endpoints)."""
        if mime_type == "application/pdf":
            return self._extract_pdf_from_bytes(content)
        elif mime_type.startswith("image/"):
            return self._extract_image_from_bytes(content)
        else:
            raise ValueError(f"Unsupported mime type: {mime_type}")

    # ─── PDF extraction ────────────────────────────────────────────────────────

    def _extract_from_pdf(self, file_path: str) -> Tuple[str, float]:
        if FITZ_AVAILABLE:
            text, conf = self._fitz_extract(file_path)
            if text.strip():
                return self._clean_text(text), conf

        if PDFPLUMBER_AVAILABLE:
            text, conf = self._pdfplumber_extract(file_path)
            if text.strip():
                return self._clean_text(text), conf

        if PYPDF_AVAILABLE:
            text, conf = self._pypdf_extract(file_path)
            if text.strip():
                return self._clean_text(text), conf

        # Last resort: EasyOCR on images rendered from PDF
        if FITZ_AVAILABLE and EASYOCR_AVAILABLE:
            return self._ocr_pdf_pages(file_path)

        return "", 0.0

    def _extract_pdf_from_bytes(self, content: bytes) -> Tuple[str, float]:
        """Extract from PDF bytes using fitz."""
        if FITZ_AVAILABLE:
            try:
                doc = fitz.open(stream=content, filetype="pdf")
                texts = []
                for page in doc:
                    texts.append(page.get_text())
                doc.close()
                text = "\n".join(texts)
                if text.strip():
                    return self._clean_text(text), 0.95
            except Exception as e:
                logger.error(f"fitz bytes extraction failed: {e}")

        if PYPDF_AVAILABLE:
            try:
                reader = PdfReader(io.BytesIO(content))
                text = "\n".join(p.extract_text() or "" for p in reader.pages)
                if text.strip():
                    return self._clean_text(text), 0.85
            except Exception as e:
                logger.error(f"pypdf bytes extraction failed: {e}")

        return "", 0.0

    def _fitz_extract(self, file_path: str) -> Tuple[str, float]:
        try:
            doc = fitz.open(file_path)
            texts = []
            for page in doc:
                texts.append(page.get_text())
            doc.close()
            return "\n".join(texts), 0.95
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            return "", 0.0

    def _pdfplumber_extract(self, file_path: str) -> Tuple[str, float]:
        try:
            with pdfplumber.open(file_path) as pdf:
                texts = [p.extract_text() or "" for p in pdf.pages]
            return "\n".join(texts), 0.9
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return "", 0.0

    def _pypdf_extract(self, file_path: str) -> Tuple[str, float]:
        try:
            reader = PdfReader(file_path)
            text = "\n".join(p.extract_text() or "" for p in reader.pages)
            return text, 0.85
        except Exception as e:
            logger.error(f"pypdf extraction failed: {e}")
            return "", 0.0

    def _ocr_pdf_pages(self, file_path: str) -> Tuple[str, float]:
        """Render PDF pages as images and run EasyOCR."""
        try:
            reader = self._get_easyocr_reader()
            if reader is None:
                return "", 0.0
            doc = fitz.open(file_path)
            all_text = []
            confidences = []
            for page in doc:
                mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                results = reader.readtext(img_bytes)
                page_text = " ".join(r[1] for r in results)
                page_conf = sum(r[2] for r in results) / len(results) if results else 0
                all_text.append(page_text)
                confidences.append(page_conf)
            doc.close()
            avg_conf = sum(confidences) / len(confidences) if confidences else 0
            return self._clean_text("\n".join(all_text)), avg_conf
        except Exception as e:
            logger.error(f"OCR PDF pages failed: {e}")
            return "", 0.0

    # ─── Image extraction ─────────────────────────────────────────────────────

    def _extract_from_image(self, file_path: str) -> Tuple[str, float]:
        reader = self._get_easyocr_reader()
        if reader is None:
            return "", 0.0
        try:
            results = reader.readtext(file_path)
            text = " ".join(r[1] for r in results)
            conf = sum(r[2] for r in results) / len(results) if results else 0
            return self._clean_text(text), conf
        except Exception as e:
            logger.error(f"EasyOCR image extraction failed: {e}")
            return "", 0.0

    def _extract_image_from_bytes(self, content: bytes) -> Tuple[str, float]:
        reader = self._get_easyocr_reader()
        if reader is None:
            return "", 0.0
        try:
            import numpy as np
            from PIL import Image
            img = Image.open(io.BytesIO(content))
            img_array = np.array(img)
            results = reader.readtext(img_array)
            text = " ".join(r[1] for r in results)
            conf = sum(r[2] for r in results) / len(results) if results else 0
            return self._clean_text(text), conf
        except Exception as e:
            logger.error(f"EasyOCR bytes extraction failed: {e}")
            return "", 0.0

    # ─── Text cleaning ─────────────────────────────────────────────────────────

    @staticmethod
    def _clean_text(text: str) -> str:
        """Remove excessive whitespace while preserving structure."""
        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Remove null bytes
        text = text.replace("\x00", "")
        # Collapse multiple blank lines to max 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Remove leading/trailing whitespace per line
        lines = [line.strip() for line in text.split("\n")]
        return "\n".join(lines).strip()

    def get_page_count(self, file_path: str) -> int:
        """Return the number of pages in a PDF."""
        if FITZ_AVAILABLE:
            try:
                doc = fitz.open(file_path)
                count = len(doc)
                doc.close()
                return count
            except Exception:
                pass
        return 1


# Module singleton
ocr_service = OCRService()
