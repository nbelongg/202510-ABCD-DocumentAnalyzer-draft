"""PDF mappings utilities for source document information"""
from typing import Dict, List, Optional
import csv
import os
from pathlib import Path
from services.logger import get_logger

logger = get_logger(__name__)


# Default PDF mappings structure
DEFAULT_PDF_INFO = {
    'sno': '',
    'title': '',
    'author_organization': '',
    'publication_year': '',
    'link': '',
    'pdf_title': ''
}


class PDFMappings:
    """Manages PDF metadata mappings"""
    
    def __init__(self, mappings_file: Optional[str] = None):
        """
        Initialize PDF mappings
        
        Args:
            mappings_file: Path to CSV file with PDF mappings
        """
        self.mappings: Dict[str, Dict] = {}
        self.mappings_file = mappings_file
        
        if mappings_file and os.path.exists(mappings_file):
            self.load_from_csv(mappings_file)
        else:
            logger.warning("pdf_mappings_not_loaded", file=mappings_file)
    
    def load_from_csv(self, csv_file: str) -> None:
        """
        Load PDF mappings from CSV file
        
        Expected CSV columns: pdf_name, sno, title, author_organization, 
                            publication_year, link
        
        Args:
            csv_file: Path to CSV file
        """
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pdf_name = row.get('pdf_name', row.get('pdf_title', ''))
                    if pdf_name:
                        self.mappings[pdf_name] = {
                            'sno': row.get('sno', ''),
                            'title': row.get('title', ''),
                            'author_organization': row.get('author_organization', ''),
                            'publication_year': row.get('publication_year', ''),
                            'link': row.get('link', ''),
                            'pdf_title': pdf_name
                        }
            logger.info("pdf_mappings_loaded", count=len(self.mappings))
        except Exception as e:
            logger.error("pdf_mappings_load_failed", error=str(e), file=csv_file)
    
    def get(self, pdf_name: str) -> Dict[str, str]:
        """
        Get mapping for a PDF
        
        Args:
            pdf_name: Name of the PDF file
            
        Returns:
            Dict with PDF information
        """
        if pdf_name in self.mappings:
            return self.mappings[pdf_name].copy()
        else:
            # Return default with pdf_title set
            info = DEFAULT_PDF_INFO.copy()
            info['pdf_title'] = pdf_name
            return info
    
    def add_mapping(self, pdf_name: str, info: Dict[str, str]) -> None:
        """
        Add or update a PDF mapping
        
        Args:
            pdf_name: PDF filename
            info: Dictionary with PDF information
        """
        self.mappings[pdf_name] = {
            'sno': info.get('sno', ''),
            'title': info.get('title', ''),
            'author_organization': info.get('author_organization', ''),
            'publication_year': info.get('publication_year', ''),
            'link': info.get('link', ''),
            'pdf_title': pdf_name
        }
        logger.debug("pdf_mapping_added", pdf_name=pdf_name)
    
    def get_all(self) -> Dict[str, Dict]:
        """Get all PDF mappings"""
        return self.mappings.copy()


def get_unique_sources(sources: List[Dict]) -> List[Dict]:
    """
    Remove duplicate sources based on pdf_title
    
    Args:
        sources: List of source dictionaries
        
    Returns:
        List of unique sources
    """
    seen = set()
    unique = []
    
    for source in sources:
        pdf_title = source.get('pdf_title', '')
        if pdf_title and pdf_title not in seen:
            seen.add(pdf_title)
            unique.append(source)
    
    return unique


# Global instance (can be initialized with environment variable path)
_pdf_mappings_instance: Optional[PDFMappings] = None


def get_pdf_mappings() -> PDFMappings:
    """
    Get global PDF mappings instance
    
    Returns:
        PDFMappings instance
    """
    global _pdf_mappings_instance
    
    if _pdf_mappings_instance is None:
        # Try to load from environment variable or default location
        mappings_file = os.getenv('PDF_MAPPINGS_FILE', None)
        _pdf_mappings_instance = PDFMappings(mappings_file)
    
    return _pdf_mappings_instance


def set_pdf_mappings_file(csv_file: str) -> None:
    """
    Set PDF mappings file and reload
    
    Args:
        csv_file: Path to CSV file
    """
    global _pdf_mappings_instance
    _pdf_mappings_instance = PDFMappings(csv_file)

