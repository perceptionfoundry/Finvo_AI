"""Professional document loading service using LangChain."""

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

from finvo_ai.core.exceptions import (
    DocumentLoaderError,
    UnsupportedFileFormatError,
    FileSizeError
)
from finvo_ai.utils.logger import get_logger
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
                
                # Fallback to simple unstructured approach (basic OCR)
                loader = UnstructuredImageLoader(
                    str(file_path),
                    # Don't specify strategy, use default
                    # languages=["eng"]  # Remove this as it might not be supported
                )
                documents = loader.load()
                
                if not documents or len(documents[0].page_content.strip()) < 10:
                    # Last resort: try with basic settings
                    loader_final = UnstructuredImageLoader(
                        str(file_path)
                        # Use minimal configuration
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
        """Extract text using direct Tesseract OCR with multiple strategies for logo text."""
        try:
            all_text_parts = []
            
            # Open and preprocess image
            with Image.open(file_path) as img:
                original_img = img.copy()
                
                # Strategy 1: Standard OCR for regular text
                if img.mode != 'L':
                    img_gray = img.convert('L')
                else:
                    img_gray = img.copy()
                
                # Enhance contrast for regular text
                import numpy as np
                img_array = np.array(img_gray)
                img_array = np.clip(img_array * 1.2, 0, 255).astype(np.uint8)
                img_enhanced = Image.fromarray(img_array)
                
                # Standard OCR config
                standard_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,$%:/-\n '
                standard_text = pytesseract.image_to_string(img_enhanced, config=standard_config)
                all_text_parts.append(("standard", standard_text))
                
                # Strategy 2: Logo/Header focused OCR (top portion of image)
                try:
                    width, height = original_img.size
                    # Extract top 25% of image where logos/merchant names usually are
                    top_region = original_img.crop((0, 0, width, height // 4))
                    
                    # Convert to grayscale and enhance for logo text
                    if top_region.mode != 'L':
                        top_region = top_region.convert('L')
                    
                    # More aggressive processing for logo text
                    top_array = np.array(top_region)
                    
                    # High contrast enhancement for logos
                    top_array = np.clip(top_array * 1.5, 0, 255).astype(np.uint8)
                    
                    # Threshold to make text more prominent
                    threshold = 128
                    top_array = np.where(top_array > threshold, 255, 0).astype(np.uint8)
                    
                    top_processed = Image.fromarray(top_array)
                    
                    # OCR config optimized for logo text (more permissive)
                    logo_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789&-.\n '
                    logo_text = pytesseract.image_to_string(top_processed, config=logo_config)
                    all_text_parts.append(("logo_region", logo_text))
                    
                except Exception as e:
                    logger.debug("Logo region extraction failed", error=str(e))
                
                # Strategy 3: Try different PSM modes for challenging text
                try:
                    # PSM 7: Single text line (good for merchant names in logos)
                    single_line_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789&-.\n '
                    single_line_text = pytesseract.image_to_string(img_enhanced, config=single_line_config)
                    all_text_parts.append(("single_line", single_line_text))
                    
                except Exception as e:
                    logger.debug("Single line extraction failed", error=str(e))
                
                # Combine all extraction results
                combined_lines = []
                for strategy, text in all_text_parts:
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    for line in lines:
                        if line not in combined_lines:  # Avoid duplicates
                            combined_lines.append(line)
                    logger.debug(f"Strategy '{strategy}' extracted {len(lines)} lines")
                
                combined_text = '\n'.join(combined_lines)
                
                logger.debug("Multi-strategy Tesseract extraction completed", 
                           total_strategies=len(all_text_parts),
                           extracted_lines=len(combined_lines), 
                           content_length=len(combined_text))
                
                return combined_text
                
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