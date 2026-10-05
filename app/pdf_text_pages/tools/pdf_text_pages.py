import time
from collections.abc import Generator
from typing import Any
from uuid import uuid4

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.file.file import File
from pdf_core.config import Limits, load_runtime_sources
from pdf_core.fetch import fetch
from pdf_core.formatting import format_text
from pdf_core.model import BatchRecord, ConversionError, InputPDF
from pdf_core.runner import convert, execution_slot


def normalize(
    parameters: dict[str, Any], limits: Limits
) -> list[tuple[str, int, File]]:
    items: list[tuple[str, int, File]] = []
    files = parameters.get("pdf_files")
    if files is not None:
        if not isinstance(files, list):
            raise ConversionError("pdf_files: INPUT: expected File list")
        if len(files) + len(items) > limits.max_files:
            raise ConversionError("LIMIT: input file count")
        items.extend(("pdf_files", index, file) for index, file in enumerate(files))
    if len(items) > limits.max_files:
        raise ConversionError("LIMIT: input file count")
    declared_total = 0
    for parameter, index, file in items:
        position = f"{parameter}[{index}]"
        if not isinstance(file, File):
            raise ConversionError(
                f"{position}: INPUT: expected Dify File (URL/path strings prohibited)"
            )
        if (file.extension or "").lower() not in (
            "pdf",
            ".pdf",
        ) and file.mime_type != "application/pdf":
            raise ConversionError(f"{position}: INPUT: only PDF files accepted")
        if file.mime_type not in (None, "application/pdf", "application/octet-stream"):
            raise ConversionError(f"{position}: INPUT: non-PDF MIME")
        if len(file.filename or "") > 4096:
            raise ConversionError(f"{position}: LIMIT: filename characters")
        if file.size is not None:
            if file.size < 0 or file.size > limits.input_file_bytes:
                raise ConversionError(f"{position}: LIMIT: declared input bytes")
            declared_total += file.size
    if declared_total > limits.input_total_bytes:
        raise ConversionError("LIMIT: declared total input bytes")
    return items


class PdfTextPagesTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        files = tool_parameters.get("pdf_files")
        if files is None or (isinstance(files, list) and not files):
            # No PDF means no source/config/DPI/slot/native work is necessary.
            # No BLOB messages preserves Dify's standard files=[] output.
            batch = BatchRecord("B" + uuid4().hex.upper(), [])
            yield self.create_text_message("")
            yield self.create_json_message(batch.metadata())
            return
        limits = Limits.from_env()
        sources = load_runtime_sources()
        dpi = limits.dpi(tool_parameters.get("dpi"))
        items = normalize(tool_parameters, limits)
        deadline = time.monotonic() + limits.request_seconds
        with execution_slot(limits):
            inputs: list[InputPDF] = []
            total = 0
            for parameter, index, file in items:
                try:
                    data = fetch(
                        file.url,
                        sources,
                        limits,
                        limits.input_total_bytes - total,
                        deadline,
                    )
                    if not data.startswith(b"%PDF-"):
                        raise ConversionError("PDF_OPEN: invalid PDF signature")
                except ConversionError as exc:
                    raise ConversionError(f"{parameter}[{index}]: {exc}") from None
                total += len(data)
                inputs.append(
                    InputPDF(file.filename or "(unnamed PDF)", parameter, index, data)
                )
            batch = convert(inputs, dpi, limits, deadline)
            text = format_text(batch, limits.text_chars)
            # Build all messages before yielding, after successful conversion.
            messages = [self.create_text_message(text)]
            messages.extend(
                self.create_blob_message(
                    page.png,
                    {
                        "mime_type": "image/png",
                        "filename": page.image_filename,
                    },
                )
                for page in batch.pages
            )
            messages.append(self.create_json_message(batch.metadata()))
            if time.monotonic() >= deadline:
                raise ConversionError("PROCESS_TIMEOUT: request deadline before output")
            for message in messages:
                if time.monotonic() >= deadline:
                    raise ConversionError("PROCESS_TIMEOUT: output deadline")
                yield message
