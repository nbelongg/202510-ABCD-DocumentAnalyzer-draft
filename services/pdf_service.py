"""PDF and document processing service"""
from typing import Optional
import pdfplumber
import docx
from io import BytesIO
from config.settings import settings
from services.logger import get_logger
from services.exceptions import FileProcessingError

logger = get_logger(__name__)


class PDFService:
    """Service for PDF and document extraction"""
    
    def __init__(self):
        """Initialize PDF service"""
        self.use_llama_parse = bool(settings.LLAMA_PARSE_API_KEY)
        if self.use_llama_parse:
            logger.info("llama_parse_enabled")
    
    def extract_text_from_pdf(self, file_data: BytesIO) -> str:
        """
        Extract text from PDF file
        
        Args:
            file_data: PDF file data
            
        Returns:
            Extracted text
        """
        try:
            logger.info("extracting_text_from_pdf")
            
            file_data.seek(0)
            text_parts = []
            
            with pdfplumber.open(file_data) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"processed_pdf_pages", count=i + 1)
            
            full_text = "\n".join(text_parts)
            
            logger.info(
                "pdf_extraction_success",
                pages=len(text_parts),
                characters=len(full_text)
            )
            
            return full_text
            
        except Exception as e:
            logger.error("pdf_extraction_failed", error=str(e))
            raise FileProcessingError(f"PDF extraction failed: {str(e)}")
    
    def extract_text_from_docx(self, file_data: BytesIO) -> str:
        """
        Extract text from DOCX file
        
        Args:
            file_data: DOCX file data
            
        Returns:
            Extracted text
        """
        try:
            logger.info("extracting_text_from_docx")
            
            file_data.seek(0)
            doc = docx.Document(file_data)
            
            text_parts = [paragraph.text for paragraph in doc.paragraphs if paragraph.text]
            full_text = "\n".join(text_parts)
            
            logger.info(
                "docx_extraction_success",
                paragraphs=len(text_parts),
                characters=len(full_text)
            )
            
            return full_text
            
        except Exception as e:
            logger.error("docx_extraction_failed", error=str(e))
            raise FileProcessingError(f"DOCX extraction failed: {str(e)}")
    
    def extract_text_from_txt(self, file_data: BytesIO) -> str:
        """
        Extract text from TXT file
        
        Args:
            file_data: TXT file data
            
        Returns:
            Extracted text
        """
        try:
            logger.info("extracting_text_from_txt")
            
            file_data.seek(0)
            text = file_data.read().decode('utf-8')
            
            logger.info("txt_extraction_success", characters=len(text))
            
            return text
            
        except Exception as e:
            logger.error("txt_extraction_failed", error=str(e))
            raise FileProcessingError(f"TXT extraction failed: {str(e)}")
    
    def extract_text(self, file_data: BytesIO, filename: str) -> str:
        """
        Extract text from file based on extension
        
        Args:
            file_data: File data
            filename: Original filename with extension
            
        Returns:
            Extracted text
        """
        try:
            file_ext = filename.lower().split('.')[-1]
            
            if file_ext == 'pdf':
                return self.extract_text_from_pdf(file_data)
            elif file_ext == 'docx':
                return self.extract_text_from_docx(file_data)
            elif file_ext == 'txt':
                return self.extract_text_from_txt(file_data)
            else:
                raise FileProcessingError(f"Unsupported file type: {file_ext}")
                
        except FileProcessingError:
            raise
        except Exception as e:
            logger.error("text_extraction_failed", error=str(e), filename=filename)
            raise FileProcessingError(f"Text extraction failed: {str(e)}")
    
    def extract_with_llama_parse(
        self,
        file_data: BytesIO,
        filename: str
    ) -> str:
        """
        Extract text using LlamaParse for better quality
        
        Args:
            file_data: File data
            filename: Original filename
            
        Returns:
            Extracted text
        """
        try:
            if not self.use_llama_parse:
                logger.warning("llama_parse_not_configured")
                return self.extract_text(file_data, filename)
            
            # Implementation would go here using LlamaParse API
            # For now, fallback to standard extraction
            logger.info("using_llama_parse_fallback")
            return self.extract_text(file_data, filename)
            
        except Exception as e:
            logger.error("llama_parse_failed", error=str(e))
            # Fallback to standard extraction
            return self.extract_text(file_data, filename)

