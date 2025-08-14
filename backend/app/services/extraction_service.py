# from typing import Dict, Any, Optional
# import logging
# import sys
# import os

# # Add the utils directory to the path to import the extraction module
# sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils', 'make_model_extraction'))

# try:
#     from make_model_extraction import extract_info
# except ImportError as e:
#     logging.error(f"Failed to import extract_info: {e}")
#     extract_info = None

# logger = logging.getLogger(__name__)

from app.utils.make_model_extraction.make_model_extraction import extract_info
from typing import Dict, Any, Optional
import logging
logger = logging.getLogger(__name__)

class ExtractionService:
    """Service for extracting make and model information from text - Singleton pattern"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ExtractionService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
    
    def extract_car_info(self, text: str) -> Dict[str, Any]:
        """
        Extract car make and model information from text
        
        Args:
            text: Input text to extract car information from
            
        Returns:
            Dictionary containing extracted car information or error details
        """
        try:
            if extract_info is None:
                return {
                    "success": False,
                    "error": "Extraction module not available",
                    "extracted_info": None
                }
            
            # Call the extract_info function
            extracted_data = extract_info(text)
            
            return {
                "success": True,
                "extracted_info": extracted_data,
                "input_text": text
            }
            
        except Exception as e:
            logger.error(f"Error extracting car info from text '{text}': {e}")
            return {
                "success": False,
                "error": str(e),
                "extracted_info": None,
                "input_text": text
            }
    