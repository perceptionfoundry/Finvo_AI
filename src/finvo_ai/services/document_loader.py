"""Professional document loading service using LangChain."""

import base64
import tempfile
from io import BytesIO
from pathlib import Path
from typing import List, Union, Optional, Dict, Any

from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredImageLoader,
    UnstructuredFileLoader
)
from langchain_core.documents import Document
from PIL import Image
import numpy as np
import pytesseract

from src.finvo_ai.core.exceptions import (
    DocumentLoaderError,
    UnsupportedFileFormatError,
    FileSizeError
)
from src.finvo_ai.utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)


class DocumentLoaderService:
    """Professional document loading service with LangChain integration."""
    
    SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    SUPPORTED_PDF_FORMATS = {'.pdf'}
    
    def __init__(self):
        """Initialize the document loader service."""
        self.max_file_size = settings.max_file_size_mb * 1024 * 1024  # Convert to bytes
        self.temp_dir = Path(settings.temp_dir)
        logger.info("Document loader service initialized", max_file_size_mb=settings.max_file_size_mb)
    
    def load_from_path(self, file_path: Union[str, Path]) -> List[Document]:
        """
        Load documents from a file path.
        
        Args:
            file_path: Path to the file to load
            
        Returns:
            List of LangChain Document objects
            
        Raises:
            DocumentLoaderError: If loading fails
            UnsupportedFileFormatError: If file format is not supported
            FileSizeError: If file is too large
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise DocumentLoaderError(f"File not found: {file_path}")
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.max_file_size:
            raise FileSizeError(
                f"File too large: {file_size / (1024*1024):.2f}MB, max: {settings.max_file_size_mb}MB"
            )
        
        file_extension = file_path.suffix.lower()
        
        try:
            if file_extension in self.SUPPORTED_PDF_FORMATS:
                return self._load_pdf(file_path)
            elif file_extension in self.SUPPORTED_IMAGE_FORMATS:
                return self._load_image(file_path)
            else:
                raise UnsupportedFileFormatError(f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            logger.error(
                "Document loading failed",
                file_path=str(file_path),
                error=str(e),
                exc_info=True
            )
            if isinstance(e, (UnsupportedFileFormatError, FileSizeError)):
                raise
            raise DocumentLoaderError(f"Failed to load document: {str(e)}") from e
    
    def load_from_bytes(
        self, 
        file_bytes: bytes, 
        filename: str, 
        mime_type: Optional[str] = None
    ) -> List[Document]:
        """
        Load documents from bytes.
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename
            mime_type: MIME type of the file
            
        Returns:
            List of LangChain Document objects
        """
        if len(file_bytes) > self.max_file_size:
            raise FileSizeError(
                f"File too large: {len(file_bytes) / (1024*1024):.2f}MB, max: {settings.max_file_size_mb}MB"
            )
        
        # Create temporary file
        file_extension = Path(filename).suffix.lower()
        
        with tempfile.NamedTemporaryFile(
            suffix=file_extension,
            dir=self.temp_dir,
            delete=False
        ) as temp_file:
            temp_file.write(file_bytes)
            temp_path = Path(temp_file.name)
        
        try:
            documents = self.load_from_path(temp_path)
            # Add metadata
            for doc in documents:
                doc.metadata.update({
                    "original_filename": filename,
                    "file_size": len(file_bytes),
                    "mime_type": mime_type
                })
            return documents
        finally:
            # Clean up temporary file
            temp_path.unlink(missing_ok=True)
    
    def load_from_base64(self, base64_data: str, filename: str) -> List[Document]:
        """
        Load documents from base64 encoded data.
        
        Args:
            base64_data: Base64 encoded file content
            filename: Original filename
            
        Returns:
            List of LangChain Document objects
        """
        try:
            file_bytes = base64.b64decode(base64_data)
            return self.load_from_bytes(file_bytes, filename)
        except Exception as e:
            raise DocumentLoaderError(f"Failed to decode base64 data: {str(e)}") from e
    
    def _load_pdf(self, file_path: Path) -> List[Document]:
        """Load PDF documents using LangChain PDF loader."""
        try:
            loader = PyPDFLoader(str(file_path))
            documents = loader.load()
            
            # Add metadata
            for i, doc in enumerate(documents):
                doc.metadata.update({
                    "source": str(file_path),
                    "file_type": "pdf",
                    "page_number": i + 1,
                    "total_pages": len(documents)
                })
            
            logger.info(f"Loaded PDF with {len(documents)} pages", file_path=str(file_path))
            return documents
            
        except Exception as e:
            raise DocumentLoaderError(f"Failed to load PDF: {str(e)}") from e
    
    def _load_image(self, file_path: Path) -> List[Document]:
        """Load image documents using fast OCR approach."""
        try:
            # Start with direct Tesseract for speed - it's often the most reliable for receipts
            logger.info("Starting with fast Tesseract OCR extraction", file_path=str(file_path))
            
            try:
                tesseract_text = self._extract_with_tesseract(file_path)
                if len(tesseract_text.strip()) > 20:  # If we got reasonable content
                    logger.info("Direct Tesseract extraction successful", 
                              content_length=len(tesseract_text.strip()))
                    documents = [Document(
                        page_content=tesseract_text,
                        metadata={"source": str(file_path), "extraction_method": "tesseract"}
                    )]
                else:
                    raise Exception("Insufficient text extracted from Tesseract")
                    
            except Exception as e:
                logger.warning("Direct Tesseract failed, trying unstructured fallback", error=str(e))
                
                # Fallback to simple unstructured approach (no heavy models)
                loader = UnstructuredImageLoader(
                    str(file_path),
                    strategy="fast",  # Fast processing, no heavy models
                    languages=["eng"]  # Use languages instead of deprecated ocr_languages
                )
                documents = loader.load()
                
                if not documents or len(documents[0].page_content.strip()) < 10:
                    # Last resort: try ocr_only strategy
                    loader_final = UnstructuredImageLoader(
                        str(file_path),
                        strategy="ocr_only",
                        languages=["eng"]
                    )
                    documents_final = loader_final.load()
                    if documents_final and len(documents_final[0].page_content.strip()) > len(documents[0].page_content.strip() if documents else ""):
                        documents = documents_final
            
            # Get image metadata
            image_metadata = self._get_image_metadata(file_path)
            
            # Add metadata to documents
            for doc in documents:
                doc.metadata.update({
                    "source": str(file_path),
                    "file_type": "image",
                    **image_metadata
                })
                
                # Log extracted content for debugging
                logger.debug("Extracted text content", 
                           file_path=str(file_path), 
                           content_preview=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                           content_length=len(doc.page_content))
            
            logger.info("Loaded image document", file_path=str(file_path), **image_metadata)
            return documents
            
        except Exception as e:
            raise DocumentLoaderError(f"Failed to load image: {str(e)}") from e
    
    def _extract_with_tesseract(self, file_path: Path) -> str:
        """Extract text using direct Tesseract OCR with financial receipt optimizations."""
        try:
            # Open and preprocess image for better OCR
            with Image.open(file_path) as img:
                # Convert to grayscale for better OCR
                if img.mode != 'L':
                    img = img.convert('L')
                
                # Enhance contrast for better text recognition
                import numpy as np
                img_array = np.array(img)
                # Simple contrast enhancement
                img_array = np.clip(img_array * 1.2, 0, 255).astype(np.uint8)
                img = Image.fromarray(img_array)
                
                # Configure Tesseract for financial documents
                custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,$%:/-\n '
                
                # Extract text
                text = pytesseract.image_to_string(img, config=custom_config)
                
                # Clean up the text
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                cleaned_text = '\n'.join(lines)
                
                logger.debug("Direct Tesseract extraction completed", 
                           extracted_lines=len(lines), 
                           content_length=len(cleaned_text))
                
                return cleaned_text
                
        except Exception as e:
            logger.error("Tesseract extraction failed", error=str(e))
            return ""
    
    def _get_image_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from image file."""
        try:
            with Image.open(file_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "file_extension": file_path.suffix.lower()
                }
        except Exception as e:
            logger.warning(f"Failed to extract image metadata: {str(e)}")
            return {
                "file_extension": file_path.suffix.lower()
            }
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return sorted(list(self.SUPPORTED_IMAGE_FORMATS | self.SUPPORTED_PDF_FORMATS))