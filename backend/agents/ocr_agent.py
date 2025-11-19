"""
OCR Agent for document processing, text extraction, and semantic search
"""

from typing import List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from pathlib import Path
from html import escape
from .base_agent import BaseAgent


OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class OCRAgent(BaseAgent):
    """OCR agent that provides PDF reader and Optical Character Recognition functionality."""
    
    def __init__(self, model: ChatOpenAI, timezone: str = "Asia/Ho_Chi_Minh"):
        super().__init__(model, timezone)
        self.name = "OCR Agent"
        self._tools = None
        self.vectorstore = None
        self.embeddings = None
        self.text_splitter = None
        self.ocr_pipeline = None
        self.processed_files = {}  # Track processed files
    
    async def initialize(self):
        """Initialize the OCR agent with PaddleOCR and vector store."""
        try:
            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=100,
                length_function=len,
            )
            
            # Try to initialize PaddleOCR
            try:
                from paddleocr import PPStructureV3
                self.ocr_pipeline = PPStructureV3(
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False
                )
                print("[OK] OCR Agent initialized with PaddleOCR")
            except ImportError:
                print("[WARNING] PaddleOCR not installed. Install with: pip install paddleocr")
                self.ocr_pipeline = None
            
            # Create tools
            self._tools = [
                self._create_ocr_tool(),
                self._create_search_document_tool(),
                self._create_list_documents_tool()
            ]
            
            print("[OK] OCR Agent initialized successfully")
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize OCR Agent: {e}")
            self._tools = [self._create_mock_ocr_tool()]
    
    def _create_ocr_tool(self):
        """Create the OCR processing tool."""
        
        @tool
        async def process_document(file_path: str, file_type: str = "auto") -> str:
            """
            Process a document (PDF or image) using OCR and store it in vector database.
            
            Args:
                file_path: Path to the file to process
                file_type: Type of file ("pdf", "image", or "auto" for auto-detection)
            
            Returns:
                Status message with extracted text summary
            """
            try:
                if not self.ocr_pipeline:
                    return "Lỗi: PaddleOCR chưa được cài đặt. Vui lòng cài đặt với: pip install paddleocr"
                
                # Validate file exists
                path = Path(file_path)
                if not path.exists():
                    return f"Lỗi: Không tìm thấy file tại đường dẫn: {file_path}"
                
                # Auto-detect file type
                if file_type == "auto":
                    suffix = path.suffix.lower()
                    if suffix == ".pdf":
                        file_type = "pdf"
                    elif suffix in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
                        file_type = "image"
                    else:
                        return f"Lỗi: Định dạng file không được hỗ trợ: {suffix}"
                
                # Process with OCR
                output = self.ocr_pipeline.predict(input=file_path)
                
                # Extract text from OCR results
                markdown_filename = f"{path.stem}.md"
                markdown_path = OUTPUT_DIR / markdown_filename
                
                # Save results to markdown files
                for res in output:
                    res.save_to_markdown(save_path=str(OUTPUT_DIR))
                
                # Read markdown file content
                if markdown_path.exists():
                    with open(markdown_path, 'r', encoding='utf-8') as f:
                        full_text = f.read()
                else:
                    full_text = ""
                
                if not full_text.strip():
                    return f"Cảnh báo: Không trích xuất được văn bản từ file: {path.name}"
                
                # Split text into chunks
                chunks = self.text_splitter.split_text(full_text)
                
                # Create metadata for chunks
                metadatas = [
                    {
                        "source": path.name,
                        "file_path": str(path),
                        "file_type": file_type,
                        "chunk_index": i
                    }
                    for i in range(len(chunks))
                ]
                
                # Create or update vector store
                if self.vectorstore is None:
                    self.vectorstore = FAISS.from_texts(
                        texts=chunks,
                        embedding=self.embeddings,
                        metadatas=metadatas
                    )
                else:
                    new_vectorstore = FAISS.from_texts(
                        texts=chunks,
                        embedding=self.embeddings,
                        metadatas=metadatas
                    )
                    self.vectorstore.merge_from(new_vectorstore)
                
                # Track processed file
                self.processed_files[path.name] = {
                    "path": str(path),
                    "type": file_type,
                    "chunks": len(chunks),
                    "char_count": len(full_text),
                    "markdown_file": markdown_filename
                }
                
                preview_html = self._render_markdown_preview(full_text)
                markdown_url = f"/api/ocr/markdown/{markdown_filename}"
                
                # Return summary
                summary = (
                    f"<div class='ocr-summary'>"
                    f"<p>✅ <strong>Xử lý thành công file:</strong> {path.name}</p>"
                    f"<ul>"
                    f"<li>Loại file: <strong>{file_type.upper()}</strong></li>"
                    f"<li>Số lượng đoạn văn bản: <strong>{len(chunks)}</strong></li>"
                    f"<li>Tổng số ký tự: <strong>{len(full_text):,}</strong></li>"
                    f"<li>File markdown: <strong>{markdown_filename}</strong></li>"
                    f"</ul>"
                    f"</div>"
                    f"<div class='ocr-preview'>"
                    f"<h3>📑 Nội dung OCR (Markdown)</h3>"
                    f"{preview_html}"
                    f"</div>"
                    f"<div class='ocr-download'>"
                    f"📎 <a href=\"{markdown_url}\" target=\"_blank\" rel=\"noopener noreferrer\">Tải file markdown vừa xử lý</a>"
                    f"<br><small>Hoặc truy cập trong thư mục output/{markdown_filename}</small>"
                    f"</div>"
                    f"<div class='ocr-tip'>"
                    f"<em>Tài liệu đã được lưu vào cơ sở dữ liệu vector. Bạn có thể tìm kiếm thông tin bằng công cụ search_document.</em>"
                    f"</div>"
                )
                
                return summary
                
            except Exception as e:
                return f"Lỗi khi xử lý tài liệu: {str(e)}"
        
        return process_document
    
    def _create_search_document_tool(self):
        """Create the document search tool."""
        
        @tool
        async def search_document(query: str, max_results: int = 3) -> str:
            """
            Search for information in processed documents using semantic search.
            
            Args:
                query: The search query
                max_results: Maximum number of results to return (default: 3)
            
            Returns:
                Relevant text chunks from documents
            """
            try:
                if self.vectorstore is None:
                    return "Chưa có tài liệu nào được xử lý. Vui lòng sử dụng process_document để tải tài liệu trước."
                
                # Perform similarity search
                results = self.vectorstore.similarity_search_with_score(
                    query=query,
                    k=max_results
                )
                
                if not results:
                    return f"Không tìm thấy kết quả nào cho truy vấn: '{query}'"
                
                # Format results
                formatted_results = []
                formatted_results.append(f"🔍 **Kết quả tìm kiếm cho: '{query}'**\n")
                
                for i, (doc, score) in enumerate(results, 1):
                    source = doc.metadata.get('source', 'Không rõ nguồn')
                    chunk_index = doc.metadata.get('chunk_index', 'N/A')
                    content = doc.page_content
                    
                    # Calculate relevance percentage (lower score = more relevant)
                    relevance = max(0, 100 - (score * 100))
                    
                    formatted_results.append(f"**{i}. Nguồn: {source}** (Đoạn #{chunk_index})")
                    formatted_results.append(f"📊 Độ liên quan: {relevance:.1f}%")
                    formatted_results.append(f"📝 Nội dung:")
                    formatted_results.append(f"{content}\n")
                
                formatted_results.append("---")
                formatted_results.append("💡 **Gợi ý:** Bạn có thể điều chỉnh truy vấn để có kết quả chính xác hơn.")
                
                return "\n".join(formatted_results)
                
            except Exception as e:
                return f"Lỗi khi tìm kiếm: {str(e)}"
        
        return search_document
    
    def _create_list_documents_tool(self):
        """Create the list documents tool."""
        
        @tool
        async def list_documents() -> str:
            """
            List all processed documents in the system.
            
            Returns:
                List of processed documents with details
            """
            try:
                if not self.processed_files:
                    return "📂 Chưa có tài liệu nào được xử lý."
                
                result = ["📚 **Danh sách tài liệu đã xử lý:**\n"]
                
                for i, (filename, info) in enumerate(self.processed_files.items(), 1):
                    result.append(f"**{i}. {filename}**")
                    result.append(f"   - Loại: {info['type'].upper()}")
                    result.append(f"   - Số đoạn: {info['chunks']}")
                    result.append(f"   - Ký tự: {info['char_count']:,}")
                    result.append(f"   - Đường dẫn: {info['path']}\n")
                
                result.append(f"**Tổng số tài liệu:** {len(self.processed_files)}")
                
                return "\n".join(result)
                
            except Exception as e:
                return f"Lỗi khi liệt kê tài liệu: {str(e)}"
        
        return list_documents
    
    def _create_mock_ocr_tool(self):
        """Create a mock OCR tool when dependencies are not available."""
        
        @tool
        async def mock_ocr(file_path: str) -> str:
            """
            Mock OCR function when dependencies are not available.
            
            Args:
                file_path: Path to the file
            
            Returns:
                Mock processing message
            """
            return f"""⚠️ **Chế độ mô phỏng OCR**

File: {file_path}

Để sử dụng chức năng OCR thực, vui lòng cài đặt:
- pip install paddleocr
- pip install paddlepaddle

Sau đó khởi động lại agent."""
        
        return mock_ocr
    
    def get_system_prompt(self) -> str:
        return """Bạn là OCR Agent chuyên về xử lý tài liệu và trích xuất văn bản.

QUY TẮC NGÔN NGỮ:
- Mặc định trả lời bằng tiếng Việt.
- Nếu người dùng hỏi bằng ngôn ngữ khác, trả lời bằng chính ngôn ngữ đó.

NHIỆM VỤ:
- Xử lý PDF và hình ảnh bằng OCR (Optical Character Recognition)
- Trích xuất văn bản từ tài liệu
- Lưu trữ văn bản vào cơ sở dữ liệu vector
- Tìm kiếm ngữ nghĩa trong tài liệu đã xử lý
- Quản lý danh sách tài liệu

CÔNG CỤ AVAILABLE:
1. process_document: Xử lý file PDF hoặc ảnh, trích xuất văn bản và lưu vào vector database
2. search_document: Tìm kiếm thông tin trong các tài liệu đã xử lý
3. list_documents: Liệt kê tất cả tài liệu đã được xử lý

QUY TRÌNH XỬ LÝ TÀI LIỆU:
1. Nhận file từ người dùng (PDF hoặc ảnh)
2. Sử dụng process_document để trích xuất văn bản
3. Văn bản được chia thành các đoạn nhỏ (chunks)
4. Mỗi đoạn được embedding và lưu vào FAISS vector store
5. File markdown được lưu tại thư mục output/

QUY TRÌNH TÌM KIẾM:
1. Nhận truy vấn từ người dùng
2. Sử dụng search_document với truy vấn
3. Tìm kiếm ngữ nghĩa trong vector database
4. Trả về các đoạn văn bản liên quan nhất
5. Hiển thị nguồn và độ liên quan

LƯU Ý:
- Hỗ trợ định dạng: PDF, JPG, PNG, BMP, TIFF
- Văn bản được chia thành chunks 500 ký tự với overlap 100 ký tự
- Sử dụng OpenAI embeddings (text-embedding-3-small)
- Vector store: FAISS cho tìm kiếm nhanh
- Luôn hiển thị nguồn tài liệu khi trả về kết quả
- Nếu không tìm thấy, gợi ý người dùng điều chỉnh truy vấn"""
    
    def get_tools(self) -> List[Any]:
        """Get available tools for this agent."""
        if self._tools is None:
            raise RuntimeError("OCR agent not initialized. Call initialize() first.")
        return self._tools

    def _render_markdown_preview(self, markdown_text: str, max_chars: int = 4000) -> str:
        """Return a safe HTML preview of the markdown file."""
        content = (markdown_text or "").strip()
        if not content:
            return "<em>Không có nội dung để hiển thị.</em>"
        
        truncated = content
        is_truncated = False
        if len(content) > max_chars:
            truncated = content[:max_chars]
            is_truncated = True
        
        escaped = escape(truncated)
        escaped = escaped.replace("\n", "<br>")
        
        warning = ""
        if is_truncated:
            warning = "<br><em>...(Đã rút gọn, hãy tải file markdown đầy đủ để xem toàn bộ nội dung.)</em>"
        
        return (
            "<pre style=\"white-space: pre-wrap; background: #111827; color: #f3f4f6; padding: 12px; "
            "border-radius: 8px; border: 1px solid #1f2937; max-height: 420px; overflow-y: auto;\">"
            f"{escaped}{warning}"
            "</pre>"
        )