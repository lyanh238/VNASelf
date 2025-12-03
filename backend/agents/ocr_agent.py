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
from langchain_core.messages import HumanMessage
import base64

from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption,InputFormat

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
                chunk_size=1024,
                chunk_overlap=200,
                length_function=len,
            )
            self.doc_converter = self._build_doc_converter()

            self._tools = [
                self._create_process_document_tool(),
                self._create_process_document_with_method_tool(),
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
            """Process PDF or image with Docling, create HTML and save text to vector store."""
            if not self.doc_converter or not self.embeddings or not self.text_splitter:
                return "Error: Docling or embeddings not initialized. Please restart agent."

            path = Path(file_path)
            if not path.exists():
                return f"Error: File not found at path: {file_path}"

            resolved_type = self._resolve_file_type(path, file_type)
            if resolved_type == "unsupported":
                return f"Error: Unsupported file format. Supported: PDF, JPG, PNG, BMP, TIFF, WEBP. Current file: {path.suffix}"

            try:
                conversion = await asyncio.to_thread(self._run_docling_pipeline, path)
            except Exception as exc:
                _log.exception("Docling conversion failed: %s", exc)
                return f"Error processing document with Docling: {exc}"

            markdown_text = conversion["markdown_text"]
            if not markdown_text.strip():
                return f"Warning: Could not extract text from file: {path.name}"

            chunks = self.text_splitter.split_text(markdown_text)
            if not chunks:
                return f"Warning: Could not create any text chunks from document: {path.name}"

            # Generate embeddings for each chunk and persist to NeonDB
            try:
                document_type = self._detect_document_type(path.name, markdown_text)
                chunk_embeddings = await asyncio.to_thread(
                    self.embeddings.embed_documents, chunks
                )
            except Exception as exc:
                _log.exception("Embedding generation failed: %s", exc)
                return f"Error creating embeddings for document: {exc}"

            if self.document_service:
                await self.document_service.save_document_chunks(
                    file_name=path.name,
                    file_path=str(path),
                    file_type=resolved_type,
                    chunks=chunks,
                    embeddings=chunk_embeddings,
                    original_file_name=path.name,
                    document_type=document_type,
                    extra_metadata={
                        "page_count": conversion["page_count"],
                        "table_count": conversion["table_count"],
                        "picture_count": conversion["picture_count"],
                        "processing_seconds": conversion["processing_seconds"],
                    },
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
                "document_type": document_type,
            }

            summary = (
                "<div class='ocr-result-container'>"
                "<div class='ocr-summary'>"
                f"<div class='ocr-header'><strong> Process Successfully:</strong> {escape(path.name)}</div>"
                "<div class='ocr-stats'>"
                f"<div class='ocr-stat-item'><span class='stat-label'>File Type:</span><span class='stat-value'>{resolved_type.upper()}</span></div>"
                f"<div class='ocr-stat-item'><span class='stat-label'>Document Type:</span><span class='stat-value'>{document_type.replace('_', ' ').title()}</span></div>"
                f"<div class='ocr-stat-item'><span class='stat-label'>Pages:</span><span class='stat-value'>{conversion['page_count']}</span></div>"
                f"<div class='ocr-stat-item'><span class='stat-label'>Tables:</span><span class='stat-value'>{conversion['table_count']}</span></div>"
                f"<div class='ocr-stat-item'><span class='stat-label'>Figures:</span><span class='stat-value'>{conversion['picture_count']}</span></div>"
                f"<div class='ocr-stat-item'><span class='stat-label'>Text Chunks:</span><span class='stat-value'>{len(chunks)}</span></div>"
                f"<div class='ocr-stat-item'><span class='stat-label'>Total Characters:</span><span class='stat-value'>{len(markdown_text):,}</span></div>"
                "</div>"
                "</div>"
                f"{iframe_html}"
                f"{download_button}"
                "<div class='ocr-tip'>"
                "<em>💡 Document has been saved to vector database. You can search information using search_document tool.</em>"
                "</div>"
                "</div>"
            )

            return summary

        return process_document

    def _create_process_document_with_method_tool(self):
        """Create tool that supports both Docling and OpenAI Vision API."""

        @tool("process_document_with_method")
        async def process_document_with_method(
            file_path: str, 
            method: str = "docling",
            user_prompt: Optional[str] = None,
            file_type: str = "auto"
        ) -> str:
            """
            Process PDF or image with selected method (docling or openai).
            
            Args:
                file_path: Đường dẫn đến file cần xử lý
                method: Phương pháp xử lý - "docling" hoặc "openai" (mặc định: "docling")
                user_prompt: Prompt tùy chỉnh từ người dùng (chỉ dùng với OpenAI)
                file_type: File type - "auto", "pdf", or "image"
            """
            path = Path(file_path)
            if not path.exists():
                return f"Error: File not found at path: {file_path}"

            resolved_type = self._resolve_file_type(path, file_type)
            if resolved_type == "unsupported":
                return f"Error: Unsupported file format. Supported: PDF, JPG, PNG, BMP, TIFF, WEBP. Current file: {path.suffix}"

            method_lower = method.lower()
            
            if method_lower == "openai":
                return await self._process_with_openai_vision(path, user_prompt, resolved_type)
            else:
                # Default to Docling
                return await self._process_with_docling(path, resolved_type)

        return process_document_with_method

    async def _process_with_docling(self, path: Path, resolved_type: str) -> str:
        """Process document using Docling."""
        if not self.doc_converter or not self.embeddings or not self.text_splitter:
            return "Lỗi: Docling hoặc embeddings chưa được khởi tạo. Vui lòng khởi động lại agent."

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

        # Generate embeddings and save to database
        try:
            document_type = self._detect_document_type(path.name, markdown_text)
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
                original_file_name=path.name,
                document_type=document_type,
                extra_metadata={
                    "page_count": conversion["page_count"],
                    "table_count": conversion["table_count"],
                    "picture_count": conversion["picture_count"],
                    "processing_seconds": conversion["processing_seconds"],
                },
            )

        html_filename = conversion["html_filename"]
        html_path = conversion["html_path"]
        html_url = f"/api/ocr/html/{html_filename}"
        
        iframe_html = self._render_html_iframe_embedded(html_url)
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
            "document_type": document_type,
            "method": "docling",
        }

        summary = (
            "<div class='ocr-result-container'>"
            "<div class='ocr-summary'>"
            f"<div class='ocr-header'><strong>✅ Xử lý thành công (Docling):</strong> {escape(path.name)}</div>"
            "<div class='ocr-stats'>"
            f"<div class='ocr-stat-item'><span class='stat-label'>Loại file:</span><span class='stat-value'>{resolved_type.upper()}</span></div>"
            f"<div class='ocr-stat-item'><span class='stat-label'>Loại tài liệu:</span><span class='stat-value'>{document_type.replace('_', ' ').title()}</span></div>"
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

    async def _process_with_openai_vision(self, path: Path, user_prompt: Optional[str], resolved_type: str) -> str:
        """Process document using OpenAI Vision API."""
        if resolved_type == "pdf":
            return "Error: OpenAI Vision API does not support PDF. Please use Docling for PDF files."

        try:
            # Read image file and encode to base64
            with open(path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Determine image MIME type
            suffix = path.suffix.lower()
            mime_type_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".bmp": "image/bmp",
                ".tiff": "image/tiff",
                ".tif": "image/tiff",
                ".webp": "image/webp"
            }
            mime_type = mime_type_map.get(suffix, "image/jpeg")
            
            # Create image URL
            image_url = f"data:{mime_type};base64,{image_data}"
            
            # Build prompt
            default_prompt = "Hãy đọc và trích xuất toàn bộ văn bản từ hình ảnh này. Trả về văn bản một cách chính xác và có cấu trúc."
            prompt = user_prompt if user_prompt else default_prompt
            
            # Use OpenAI Vision API
            messages = [
                HumanMessage(
                    content=[
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                )
            ]
            
            response = await self.model.ainvoke(messages)
            extracted_text = response.content if hasattr(response, 'content') else str(response)
            
            if not extracted_text.strip():
                return f"Warning: Could not extract text from file: {path.name}"
            
            # Split text into chunks and create embeddings
            chunks = self.text_splitter.split_text(extracted_text)
            if not chunks:
                return f"Warning: Could not create any text chunks from document: {path.name}"
            
            # Generate embeddings and save to database
            try:
                document_type = self._detect_document_type(path.name, extracted_text)
                chunk_embeddings = await asyncio.to_thread(
                    self.embeddings.embed_documents, chunks
                )
            except Exception as exc:
                _log.exception("Embedding generation failed: %s", exc)
                return f"Error creating embeddings for document: {exc}"
            
            if self.document_service:
                await self.document_service.save_document_chunks(
                    file_name=path.name,
                    file_path=str(path),
                    file_type=resolved_type,
                    chunks=chunks,
                    embeddings=chunk_embeddings,
                    original_file_name=path.name,
                    document_type=document_type,
                    extra_metadata={
                        "method": "openai_vision",
                        "user_prompt": user_prompt,
                    },
                )
            
            # Store in processed_files
            self.processed_files[path.name] = {
                "path": str(path),
                "type": resolved_type,
                "chunks": len(chunks),
                "char_count": len(extracted_text),
                "html_file": None,
                "html_path": None,
                "pages": 1,
                "tables": 0,
                "figures": 0,
                "processing_seconds": 0,
                "document_type": document_type,
                "method": "openai_vision",
            }
            
            summary = (
                "<div class='ocr-result-container'>"
                "<div class='ocr-summary'>"
                f"<div class='ocr-header'><strong>✅ Xử lý thành công (OpenAI Vision):</strong> {escape(path.name)}</div>"
                "<div class='ocr-stats'>"
                f"<div class='ocr-stat-item'><span class='stat-label'>Loại file:</span><span class='stat-value'>{resolved_type.upper()}</span></div>"
                f"<div class='ocr-stat-item'><span class='stat-label'>Loại tài liệu:</span><span class='stat-value'>{document_type.replace('_', ' ').title()}</span></div>"
                f"<div class='ocr-stat-item'><span class='stat-label'>Text Chunks:</span><span class='stat-value'>{len(chunks)}</span></div>"
                f"<div class='ocr-stat-item'><span class='stat-label'>Total Characters:</span><span class='stat-value'>{len(extracted_text):,}</span></div>"
                "</div>"
                "</div>"
                "<div class='ocr-extracted-text' style='margin: 16px 0; padding: 12px; background: #1e293b; border-radius: 8px; border: 1px solid #374151;'>"
                "<div style='font-weight: bold; margin-bottom: 8px; color: #f8fafc;'>📝 Extracted Text:</div>"
                f"<div style='color: #e2e8f0; white-space: pre-wrap; max-height: 400px; overflow-y: auto;'>{escape(extracted_text[:2000])}{'...' if len(extracted_text) > 2000 else ''}</div>"
                "</div>"
                "<div class='ocr-tip'>"
                "<em>💡 Text has been saved to vector database. You can search information using search_document tool.</em>"
                "</div>"
                "</div>"
            )
            
            return summary
            
        except Exception as exc:
            _log.exception("OpenAI Vision processing failed: %s", exc)
            return f"Lỗi khi xử lý hình ảnh bằng OpenAI Vision: {exc}"

    def _create_search_document_tool(self):
        """Create the semantic search tool."""

        @tool("search_document")
        async def search_document(query: str, max_results: int = 3) -> str:
            """Tìm kiếm ngữ nghĩa trong các tài liệu Docling đã xử lý."""
            if not self.document_service:
                return "Document service chưa được cấu hình. Vui lòng kiểm tra lại."

            stored_chunks = await self.document_service.get_document_chunks(limit=2000)
            if not stored_chunks:
                return "No documents have been processed yet. Please use process_document first."

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
                return "No suitable documents found for search."

            scored_results.sort(key=lambda item: item[1], reverse=True)
            top_results = scored_results[:max_results]

            formatted_results = [f"🔍 **Search results for: '{query}'**\n"]
            for idx, (chunk, similarity) in enumerate(top_results, 1):
                file_name = chunk.get("file_name", "Unknown source")
                file_path = chunk.get("file_path", "Unknown path")
                chunk_index = chunk.get("chunk_index", "N/A")
                content = chunk.get("content", "")
                relevance = max(0.0, similarity * 100)

                formatted_results.append(f"**{idx}. Source: {file_name}**")
                formatted_results.append(f"📊 Relevance: {relevance:.1f}%")
                formatted_results.append(f"📍 Location: {file_path} — Chunk #{chunk_index}")
                formatted_results.append("📝 Reference Content:")
                formatted_results.append(f"{content}\n")

            formatted_results.append("---")
            formatted_results.append("💡 **Suggestion:** Refine your query for more accurate results.")

            return "\n".join(formatted_results)

        return search_document

    def _create_list_documents_tool(self):
        """Create the listing tool for processed documents."""

        @tool("list_documents")
        async def list_documents() -> str:
            """List documents processed via Docling."""
            if not self.processed_files:
                return "📂 No documents have been processed yet."

            lines = ["📚 **List of processed documents:**\n"]
            for idx, (filename, info) in enumerate(self.processed_files.items(), 1):
                lines.append(f"**{idx}. {filename}**")
                lines.append(f"   - Type: {info['type'].upper()}")
                lines.append(f"   - Pages: {info['pages']}")
                lines.append(f"   - Text Chunks: {info['chunks']}")
                lines.append(f"   - Characters: {info['char_count']:,}")
                lines.append(f"   - HTML File: {info['html_file']}")
                doc_type = info.get("document_type", "general")
                lines.append(f"   - Document Type: {doc_type.replace('_', ' ').title()}")
                lines.append(f"   - Source Path: {info['path']}\n")

            lines.append(f"**Total documents:** {len(self.processed_files)}")
            return "\n".join(lines)

        return list_documents

    def _create_mock_tool(self, reason: str):
        """Fallback tool when Docling pipeline is unavailable."""

        @tool("mock_ocr")
        async def mock_ocr(file_path: str) -> str:
            return (
                "⚠️ **Docling Mock Mode**\n\n"
                f"File: {file_path}\n\n"
                "Docling is not available. Please install required dependencies and restart agent.\n"
                f"Reason: {reason}"
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
        return """You are an OCR Agent using Docling to process documents and images.

LANGUAGE RULES:
- By default, respond in Vietnamese.
- If user asks in a different language, respond in that same language.

TASKS:
- Process PDF and images (JPG, PNG, BMP, TIFF, WEBP) using Docling and extract visual HTML.
- Split text into small chunks, create embeddings with text-embedding-3-small and save to NeonDB for RAG.
- Provide semantic search capability on processed documents.
- List and manage processed document list.

TOOLS:
1. process_document: Process PDF or image file with Docling, create downloadable HTML and save embeddings.
2. process_document_with_method: Process file with selected method (docling or openai). Supports custom prompts for OpenAI.
3. search_document: Semantic search in processed documents.
4. list_documents: List processed documents with statistics.

PROCESS:
1. User uploads PDF or image.
2. Docling converts to HTML + text.
3. Text is split into chunks (512 characters, 128 overlap) and embedded with text-embedding-3-small.
4. Embeddings are saved to documents table on NeonDB and HTML is displayed for download.
5. User can search or list documents.

NOTES:
- Supported formats: PDF, JPG, PNG, BMP, TIFF, WEBP.
- Docling: Good for PDF and complex documents, creates visual HTML.
- OpenAI Vision: Good for simple images, supports custom prompts, remembers context.
- Prioritize displaying HTML download link and quick preview iframe (only with Docling).
- Always notify document source when returning search results.
- Suggest users refine query if no results.
- When user uploads image and requests processing with prompt, use process_document_with_method with method="openai"."""

    def get_tools(self) -> List[Any]:
        if self._tools is None:
            raise RuntimeError("OCR agent not initialized. Call initialize() first.")
        return self._tools

    @staticmethod
    def _detect_document_type(file_name: str, markdown_text: str) -> str:
        """Infer document type using filename and extracted text."""
        lookup = [
            ("curriculum vitae", "cv"),
            ("curriculum-vitae", "cv"),
            ("resume", "cv"),
            ("cover letter", "cover_letter"),
            ("research", "research_paper"),
            ("doi", "research_paper"),
            ("journal", "research_paper"),
            ("paper", "research_paper"),
            ("invoice", "invoice"),
            ("receipt", "receipt"),
            ("bill of lading", "logistics"),
            ("contract", "contract"),
            ("agreement", "contract"),
            ("proposal", "proposal"),
            ("report", "report"),
            ("presentation", "presentation"),
            ("specification", "specification"),
            ("technical", "technical_document"),
        ]

        haystack = f"{file_name}\n{markdown_text[:4000]}".lower()
        for keyword, doc_type in lookup:
            if keyword in haystack:
                return doc_type
        return "general"

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
            return "<em>Cannot read HTML file for display.</em>"

        truncated = content[:max_chars]
        is_truncated = len(content) > max_chars
        warning = ""
        if is_truncated:
            warning = "<br><em>...(Truncated, please open HTML file to view full content.)</em>"

        escaped_html = escape(truncated)
        return (
            "<details class='ocr-html-source'>"
            "<summary>View HTML Code (truncated)</summary>"
            "<pre style=\"white-space: pre-wrap; background: #0f172a; color: #f8fafc; padding: 12px; "
            "border-radius: 8px; border: 1px solid #1e293b; max-height: 360px; overflow-y: auto;\">"
            f"{escaped_html}{warning}"
            "</pre>"
            "</details>"
        )

    @staticmethod
    def _render_html_iframe_embedded(html_url: str) -> str:
        """Render iframe with HTML content using API endpoint."""
        safe_url = escape(html_url)
        return (
            "<div class='ocr-preview' style=\"margin: 16px 0;\">"
            f"<iframe src=\"{safe_url}\" "
            "style=\"width: 100%; min-height: 500px; max-height: 800px; border: 1px solid #374151; "
            "border-radius: 8px; background: #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.1);\" "
            "loading=\"lazy\" referrerpolicy=\"no-referrer\" "
            "sandbox=\"allow-same-origin allow-scripts allow-popups allow-forms\">"
            "Your browser does not support iframe."
            "</iframe>"
            "</div>"
        )
    
    @staticmethod
    def _render_download_button(filename: str, html_url: str) -> str:
        """Render download button using API endpoint."""
        if not html_url:
            return "<div class='ocr-download'><em>⚠️ Cannot create download button.</em></div>"
        
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
            "<small>HTML file contains all processed content and can be viewed directly in browser.</small>"
            "</div>"
            "</div>"
        )
