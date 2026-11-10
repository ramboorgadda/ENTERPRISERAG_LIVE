from pathlib import Path
import re
import sys

from docling.chunking import HybridChunker
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from loguru import logger

class DocumentProcessor:
    def __init__(self):
        pipeline_options = PdfPipelineOptions()
        # Avoid hard-coding MPS so ingestion works on Windows/Linux too.
        default_device = getattr(AcceleratorDevice, "AUTO", None)
        if default_device is None:
            default_device = AcceleratorDevice.CPU
        if sys.platform != "darwin":
            default_device = AcceleratorDevice.CPU
        pipeline_options.accelerator_options = AcceleratorOptions(
            num_threads=8, device=default_device
        )
        self.converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
        )
        self.chunker = HybridChunker()

    def _fallback_text_chunks(self, file_path: Path) -> list[dict]:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        if file_path.suffix.lower() in {".html", ".htm"}:
            text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return []

        source_name = file_path.name
        chunk_size = 1200
        return [
            {"text": text[i:i + chunk_size], "source": source_name}
            for i in range(0, len(text), chunk_size)
        ]

    
    def process_document(self, file_path: str) -> list[dict]:
        path = Path(file_path)
        if path.suffix.lower() in {".txt", ".md", ".html", ".htm"}:
            chunks = self._fallback_text_chunks(path)
            logger.info("Processed {} chunks from {}", len(chunks), file_path)
            return chunks

        result = self.converter.convert(file_path)
        doc = result.document
        chunk_iter = self.chunker.chunk(doc)

        chunks = []
        source_name = path.name

        for chunk in chunk_iter:
            meta = {"text": chunk.text, "source": source_name}
            if hasattr(chunk, "meta") and hasattr(chunk.meta, "doc_items"):
                items = chunk.meta.doc_items
                if items and hasattr(items[0], "prov") and items[0].prov:
                    meta["page_number"] = items[0].prov[0].page_no
            chunks.append(meta)
        logger.info("Processed {} chunks from {}", len(chunks), file_path)
        return chunks

                