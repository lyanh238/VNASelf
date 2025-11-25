"""Docling-powered OCR agent that extracts structured text and searchable HTML."""

from __future__ import annotations

import asyncio
import logging
import time
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from services.document_service import DocumentService
from .base_agent import BaseAgent

_log = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_RESOLUTION_SCALE = 2.0
SUPPORTED_PDF_SUFFIXES = {".pdf"}
SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
SUPPORTED_SUFFIXES = SUPPORTED_PDF_SUFFIXES | SUPPORTED_IMAGE_SUFFIXES


class OCRAgent(BaseAgent):
    """OCR agent that leverages Docling for PDF understanding, HTML export, and search."""

    def __init__(
        self,
        model: ChatOpenAI,
        document_service: Optional[DocumentService] = None,
        timezone: str = "Asia/Ho_Chi_Minh",
    ):
        super().__init__(model, timezone)
        self.name = "OCR Agent"
        self._tools: Optional[List[Any]] = None
        self.embeddings: Optional[OpenAIEmbeddings] = None
        self.text_splitter: Optional[RecursiveCharacterTextSplitter] = None
        self.doc_converter: Optional[DocumentConverter] = None
        self.processed_files: Dict[str, Dict[str, Any]] = {}
        self.document_service = document_service

    async def initialize(self):
        """Initialize the OCR agent with Docling and embedding utilities."""
        if self._tools is not None:
            return

        try:
            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=512,
                chunk_overlap=128,
                length_function=len,
            )
            self.doc_converter = self._build_doc_converter()

            self._tools = [
                self._create_process_document_tool(),
                self._create_search_document_tool(),
                self._create_list_documents_tool(),
            ]

            _log.info("[OK] OCR Agent initialized with Docling pipeline")
        except Exception as exc:
            _log.exception("Failed to initialize OCR Agent: %s", exc)
            self._tools = [self._create_mock_tool(str(exc))]

    def _build_doc_converter(self) -> DocumentConverter:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
        pipeline_options.generate_page_images = True
        pipeline_options.generate_picture_images = True

        return DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def _create_process_document_tool(self):
        """Create the Docling-backed document processing tool."""

        @tool("process_document")
        async def process_document(file_path: str, file_type: str = "auto") -> str:
            """Xử lý PDF hoặc ảnh với Docling, tạo HTML và lưu văn bản vào vector store."""
            if not self.doc_converter or not self.embeddings or not self.text_splitter:
                return "Lỗi: Docling hoặc embeddings chưa được khởi tạo. Vui lòng khởi động lại agent."

            path = Path(file_path)
            if not path.exists():
                return f"Lỗi: Không tìm thấy file tại đường dẫn: {file_path}"

            resolved_type = self._resolve_file_type(path, file_type)
            if resolved_type == "unsupported":
                return f"Lỗi: Định dạng file không được hỗ trợ. Hỗ trợ: PDF, JPG, PNG, BMP, TIFF, WEBP. File hiện tại: {path.suffix}"

            try:
                conversion = await asyncio.to_thread(self._run_docling_pipeline, path)
            except Exception as exc:
                _log.exception("Docling conversion failed: %s", exc)
                return f"Lỗi khi xử lý tài liệu bằng Docling: {exc}"

            markdown_text = conversion["markdown_text"]
            if not markdown_text.strip():
                return f"Cảnh báo: Không trích xuất được văn bản từ file: {path.name}"

            chunks = self.text_splitter.split_text(markdown_text)
            if not chunks:
                return f"Cảnh báo: Không tạo được đoạn văn bản nào từ tài liệu: {path.name}"

            # Generate embeddings for each chunk and persist to NeonDB
            try:
                chunk_embeddings = await asyncio.to_thread(
                    self.embeddings.embed_documents, chunks
                )
            except Exception as exc:
                _log.exception("Embedding generation failed: %s", exc)
                return f"Lỗi khi tạo embedding cho tài liệu: {exc}"

            if self.document_service:
                await self.document_service.save_document_chunks(
                    file_name=path.name,
                    file_path=str(path),
                    file_type=resolved_type,
                    chunks=chunks,
                    embeddings=chunk_embeddings,
                )

            html_filename = conversion["html_filename"]
            html_path = conversion["html_path"]
            html_url = f"/api/ocr/html/{html_filename}"
            
            # Create iframe preview using API endpoint (more reliable than data URL)
            iframe_html = self._render_html_iframe_embedded(html_url)
            
            # Create download button using API endpoint
            download_button = self._render_download_button(html_filename, html_url)

            self.processed_files[path.name] = {
                "path": str(path),
                "type": resolved_type,
                "chunks": len(chunks),
                "char_count": len(markdown_text),
                "html_file": html_filename,
                "html_path": str(html_path),
                "pages": conversion["page_count"],
                "tables": conversion["table_count"],
                "figures": conversion["picture_count"],
                "processing_seconds": conversion["processing_seconds"],
            }

            summary = (
                "<div class='ocr-result-container'>"
                "<div class='ocr-summary'>"
                f"<div class='ocr-header'><strong>✅ Xử lý thành công:</strong> {escape(path.name)}</div>"
                "<div class='ocr-stats'>"
                f"<div class='ocr-stat-item'><span class='stat-label'>Loại file:</span><span class='stat-value'>{resolved_type.upper()}</span></div>"
                f"<div class='ocr-stat-item'><span class='stat-label'>Số trang:</span><span class='stat-value'>{conversion['page_count']}</span></div>"
                f"<div class='ocr-stat-item'><span class='stat-label'>Số bảng:</span><span class='stat-value'>{conversion['table_count']}</span></div>"
                f"<div class='ocr-stat-item'><span class='stat-label'>Số hình:</span><span class='stat-value'>{conversion['picture_count']}</span></div>"
                f"<div class='ocr-stat-item'><span class='stat-label'>Đoạn văn bản:</span><span class='stat-value'>{len(chunks)}</span></div>"
                f"<div class='ocr-stat-item'><span class='stat-label'>Tổng ký tự:</span><span class='stat-value'>{len(markdown_text):,}</span></div>"
                "</div>"
                "</div>"
                f"{iframe_html}"
                f"{download_button}"
                "<div class='ocr-tip'>"
                "<em>💡 Tài liệu đã được lưu vào cơ sở dữ liệu vector. Bạn có thể tìm kiếm thông tin bằng công cụ search_document.</em>"
                "</div>"
                "</div>"
            )

            return summary

        return process_document

    def _create_search_document_tool(self):
        """Create the semantic search tool."""

        @tool("search_document")
        async def search_document(query: str, max_results: int = 3) -> str:
            """Tìm kiếm ngữ nghĩa trong các tài liệu Docling đã xử lý."""
            if not self.document_service:
                return "Document service chưa được cấu hình. Vui lòng kiểm tra lại."

            stored_chunks = await self.document_service.get_document_chunks(limit=2000)
            if not stored_chunks:
                return "Chưa có tài liệu nào được xử lý. Vui lòng sử dụng process_document trước."

            try:
                query_embedding = await asyncio.to_thread(
                    self.embeddings.embed_query, query
                )
            except Exception as exc:
                _log.exception("Query embedding failed: %s", exc)
                return f"Lỗi khi tạo embedding cho truy vấn: {exc}"

            scored_results = []
            for chunk in stored_chunks:
                embedding = chunk.get("embedding")
                content = chunk.get("content", "")
                if not embedding or not content:
                    continue
                similarity = self._cosine_similarity(query_embedding, embedding)
                scored_results.append((chunk, similarity))

            if not scored_results:
                return "Không tìm thấy tài liệu phù hợp để tìm kiếm."

            scored_results.sort(key=lambda item: item[1], reverse=True)
            top_results = scored_results[:max_results]

            formatted_results = [f"🔍 **Kết quả tìm kiếm cho: '{query}'**\n"]
            for idx, (chunk, similarity) in enumerate(top_results, 1):
                file_name = chunk.get("file_name", "Không rõ nguồn")
                file_path = chunk.get("file_path", "Không rõ đường dẫn")
                chunk_index = chunk.get("chunk_index", "N/A")
                content = chunk.get("content", "")
                relevance = max(0.0, similarity * 100)

                formatted_results.append(f"**{idx}. Nguồn: {file_name}**")
                formatted_results.append(f"📊 Độ liên quan: {relevance:.1f}%")
                formatted_results.append(f"📍 Vị trí: {file_path} — Đoạn #{chunk_index}")
                formatted_results.append("📝 Nội dung tham chiếu:")
                formatted_results.append(f"{content}\n")

            formatted_results.append("---")
            formatted_results.append("💡 **Gợi ý:** Hãy tinh chỉnh truy vấn để có kết quả chính xác hơn.")

            return "\n".join(formatted_results)

        return search_document

    def _create_list_documents_tool(self):
        """Create the listing tool for processed documents."""

        @tool("list_documents")
        async def list_documents() -> str:
            """Liệt kê các tài liệu đã xử lý qua Docling."""
            if not self.processed_files:
                return "📂 Chưa có tài liệu nào được xử lý."

            lines = ["📚 **Danh sách tài liệu đã xử lý:**\n"]
            for idx, (filename, info) in enumerate(self.processed_files.items(), 1):
                lines.append(f"**{idx}. {filename}**")
                lines.append(f"   - Loại: {info['type'].upper()}")
                lines.append(f"   - Số trang: {info['pages']}")
                lines.append(f"   - Đoạn văn bản: {info['chunks']}")
                lines.append(f"   - Ký tự: {info['char_count']:,}")
                lines.append(f"   - File HTML: {info['html_file']}")
                lines.append(f"   - Đường dẫn nguồn: {info['path']}\n")

            lines.append(f"**Tổng số tài liệu:** {len(self.processed_files)}")
            return "\n".join(lines)

        return list_documents

    def _create_mock_tool(self, reason: str):
        """Fallback tool when Docling pipeline is unavailable."""

        @tool("mock_ocr")
        async def mock_ocr(file_path: str) -> str:
            return (
                "⚠️ **Chế độ mô phỏng Docling**\n\n"
                f"File: {file_path}\n\n"
                "Docling chưa khả dụng. Vui lòng cài đặt các phụ thuộc cần thiết và khởi động lại agent.\n"
                f"Lý do: {reason}"
            )

        return mock_ocr

    def _resolve_file_type(self, path: Path, requested_type: str) -> str:
        if requested_type and requested_type.lower() != "auto":
            return requested_type.lower()

        suffix = path.suffix.lower()
        if suffix in SUPPORTED_PDF_SUFFIXES:
            return "pdf"
        elif suffix in SUPPORTED_IMAGE_SUFFIXES:
            return "image"
        return "unsupported"

    def _run_docling_pipeline(self, path: Path) -> Dict[str, Any]:
        if not self.doc_converter:
            raise RuntimeError("Docling converter is not initialized.")

        start_time = time.time()
        conv_res = self.doc_converter.convert(path)
        doc_filename = path.stem

        html_filename = f"{doc_filename}.html"
        html_path = OUTPUT_DIR / html_filename
        conv_res.document.save_as_html(html_path, image_mode=ImageRefMode.EMBEDDED)

        tmp_markdown_path = OUTPUT_DIR / f".{doc_filename}.{int(start_time)}.md"
        conv_res.document.save_as_markdown(
            tmp_markdown_path,
            image_mode=ImageRefMode.EMBEDDED,
        )

        markdown_text = ""
        if tmp_markdown_path.exists():
            markdown_text = tmp_markdown_path.read_text(encoding="utf-8")
            tmp_markdown_path.unlink(missing_ok=True)

        page_count = len(conv_res.document.pages)
        table_count = 0
        picture_count = 0
        for element, _ in conv_res.document.iterate_items():
            if isinstance(element, TableItem):
                table_count += 1
            elif isinstance(element, PictureItem):
                picture_count += 1

        processing_seconds = time.time() - start_time

        return {
            "html_filename": html_filename,
            "html_path": html_path,
            "markdown_text": markdown_text,
            "page_count": page_count,
            "table_count": table_count,
            "picture_count": picture_count,
            "processing_seconds": processing_seconds,
        }

    def get_system_prompt(self) -> str:
        return """Bạn là OCR Agent sử dụng Docling để xử lý tài liệu và hình ảnh.

QUY TẮC NGÔN NGỮ:
- Mặc định trả lời bằng tiếng Việt.
- Nếu người dùng hỏi bằng ngôn ngữ khác, trả lời bằng chính ngôn ngữ đó.

NHIỆM VỤ:
- Xử lý PDF và hình ảnh (JPG, PNG, BMP, TIFF, WEBP) bằng Docling và trích xuất HTML trực quan.
- Chia văn bản thành các đoạn nhỏ, tạo embedding bằng text-embedding-3-small và lưu vào NeonDB để phục vụ RAG.
- Cung cấp khả năng tìm kiếm ngữ nghĩa trên các tài liệu đã xử lý.
- Liệt kê và quản lý danh sách tài liệu đã xử lý.

CÔNG CỤ:
1. process_document: Xử lý file PDF hoặc ảnh, tạo HTML có thể tải xuống và lưu embeddings.
2. search_document: Tìm kiếm ngữ nghĩa trong các tài liệu Docling đã xử lý.
3. list_documents: Liệt kê các tài liệu đã xử lý cùng thống kê.

QUY TRÌNH:
1. Người dùng tải lên PDF hoặc hình ảnh.
2. Docling chuyển đổi sang HTML + văn bản.
3. Văn bản được chia thành đoạn (chunk 512 ký tự, overlap 128) và embedding với text-embedding-3-small.
4. Embedding được lưu vào bảng documents trên NeonDB và hiển thị HTML để tải xuống.
5. Người dùng có thể tìm kiếm hoặc liệt kê tài liệu.

LƯU Ý:
- Hỗ trợ định dạng: PDF, JPG, PNG, BMP, TIFF, WEBP.
- Ưu tiên hiển thị link tải HTML và iframe xem nhanh.
- Luôn thông báo nguồn tài liệu khi trả kết quả tìm kiếm.
- Gợi ý người dùng tinh chỉnh truy vấn nếu không có kết quả."""

    def get_tools(self) -> List[Any]:
        if self._tools is None:
            raise RuntimeError("OCR agent not initialized. Call initialize() first.")
        return self._tools

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def _render_html_preview(self, html_path: Path, max_chars: int = 4000) -> str:
        try:
            content = html_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return "<em>Không thể đọc file HTML để hiển thị.</em>"

        truncated = content[:max_chars]
        is_truncated = len(content) > max_chars
        warning = ""
        if is_truncated:
            warning = "<br><em>...(Đã rút gọn, hãy mở file HTML để xem đầy đủ nội dung.)</em>"

        escaped_html = escape(truncated)
        return (
            "<details class='ocr-html-source'>"
            "<summary>Xem mã HTML (đã rút gọn)</summary>"
            "<pre style=\"white-space: pre-wrap; background: #0f172a; color: #f8fafc; padding: 12px; "
            "border-radius: 8px; border: 1px solid #1e293b; max-height: 360px; overflow-y: auto;\">"
            f"{escaped_html}{warning}"
            "</pre>"
            "</details>"
        )

    @staticmethod
    def _render_html_iframe_embedded(html_url: str) -> str:
        """Render iframe with HTML content using API endpoint."""
        return (
            "<div class='ocr-preview' style=\"margin: 16px 0;\">"
            "style=\"width: 100%; min-height: 500px; max-height: 800px; border: 1px solid #374151; "
            "border-radius: 8px; background: #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.1);\" "
            "loading=\"lazy\" referrerpolicy=\"no-referrer\" "
            "sandbox=\"allow-same-origin allow-scripts allow-popups allow-forms\">"
            "Trình duyệt của bạn không hỗ trợ iframe."
            "</iframe>"
            "</div>"
        )
    
    @staticmethod
    def _render_download_button(filename: str, html_url: str) -> str:
        """Render download button using API endpoint."""
        if not html_url:
            return "<div class='ocr-download'><em>⚠️ Không thể tạo nút tải xuống.</em></div>"
        
        # Escape filename for HTML attribute
        safe_filename = escape(filename)
        safe_url = escape(html_url)
        
        # Create download button that uses JavaScript to download from API endpoint
        button_id = f"download-btn-{filename.replace('.', '-').replace('_', '-').replace(' ', '-')}"
        return (
            "<div class='ocr-download-container'>"
            "<div class='ocr-download-header'>"
            "</div>"
            f"<button "
            f"class='ocr-download-btn' "
            f"id=\"{button_id}\" "
            f"onclick=\""
            f"(function(){{"
            f"  const link = document.createElement('a'); "
            f"  link.href = '{safe_url}'; "
            f"  link.download = '{safe_filename}'; "
            f"  document.body.appendChild(link); "
            f"  link.click(); "
            f"  document.body.removeChild(link);"
            f"}})();"
            f"this.style.transform='scale(0.95)'; setTimeout(() => this.style.transform='scale(1)', 150);"
            f"\">"
            "<span class='download-btn-icon'>⬇</span>"
            "</button>"
            "<div class='ocr-download-info'>"
            "<small>File HTML chứa toàn bộ nội dung đã xử lý và có thể xem trực tiếp trên trình duyệt.</small>"
            "</div>"
            "</div>"
        )
