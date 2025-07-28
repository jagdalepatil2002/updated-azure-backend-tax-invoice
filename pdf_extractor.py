# pdf_extractor.py - Enhanced PDF Text Extraction Module
import fitz  # PyMuPDF
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def extract_text_from_pdf_enhanced(pdf_bytes: bytes) -> Optional[str]:
    """Enhanced PDF text extraction with multiple strategies."""
    if not pdf_bytes:
        logger.error("No PDF bytes provided")
        return None
        
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            logger.info(f"Processing PDF with {len(doc)} pages")
            
            # Strategy 1: Standard text extraction
            extracted_text = ""
            pages_with_text = 0
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = ""
                
                # Method 1: Standard extraction
                try:
                    page_text = page.get_text()
                    if page_text.strip():
                        pages_with_text += 1
                except Exception as e:
                    logger.warning(f"Standard extraction failed for page {page_num}: {e}")
                
                # Method 2: Dictionary-based extraction
                if not page_text.strip():
                    try:
                        text_dict = page.get_text("dict")
                        page_text = extract_text_from_dict(text_dict)
                        if page_text.strip():
                            pages_with_text += 1
                    except Exception as e:
                        logger.warning(f"Dict extraction failed for page {page_num}: {e}")
                
                # Method 3: Layout preservation
                if not page_text.strip():
                    try:
                        page_text = page.get_text("text", flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE)
                        if page_text.strip():
                            pages_with_text += 1
                    except Exception as e:
                        logger.warning(f"Layout extraction failed for page {page_num}: {e}")
                
                extracted_text += page_text + "\n\n"
            
            # Clean extracted text
            extracted_text = clean_extracted_text(extracted_text)
            
            # Check if meaningful
            if is_meaningful_text(extracted_text) and pages_with_text > 0:
                logger.info(f"Standard extraction successful: {len(extracted_text)} chars")
                return extracted_text
            
            # Strategy 2: OCR fallback
            logger.info("Attempting OCR fallback...")
            ocr_text = extract_text_with_ocr(doc)
            
            if ocr_text and is_meaningful_text(ocr_text):
                logger.info(f"OCR extraction successful: {len(ocr_text)} chars")
                return ocr_text
            
            # Return best available
            if extracted_text.strip():
                logger.warning("Returning potentially incomplete text")
                return extracted_text
            elif ocr_text and ocr_text.strip():
                logger.warning("Returning OCR text")
                return ocr_text
            
            logger.error("All extraction methods failed")
            return None
            
    except Exception as e:
        logger.error(f"PDF processing error: {e}")
        return None

def extract_text_from_dict(text_dict: dict) -> str:
    """Extract text from PyMuPDF dictionary format."""
    text_parts = []
    
    try:
        if "blocks" in text_dict:
            for block in text_dict["blocks"]:
                block_text = ""
                
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        if "spans" in line:
                            for span in line["spans"]:
                                if "text" in span:
                                    line_text += span["text"]
                        if line_text.strip():
                            block_text += line_text + "\n"
                
                elif "text" in block:
                    block_text = block["text"]
                
                if block_text.strip():
                    text_parts.append(block_text)
    
    except Exception as e:
        logger.warning(f"Error extracting from dict: {e}")
    
    return "\n".join(text_parts)

def extract_text_with_ocr(doc) -> Optional[str]:
    """Extract text using OCR."""
    try:
        try:
            import pytesseract
            from PIL import Image, ImageEnhance
            import io
        except ImportError:
            logger.warning("OCR libraries not available")
            return None
        
        extracted_text = ""
        successful_pages = 0
        
        for page_num in range(len(doc)):
            try:
                page = doc[page_num]
                
                # Convert to high-res image
                zoom_matrix = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=zoom_matrix)
                img_bytes = pix.tobytes("png")
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(img_bytes))
                
                # Enhance for OCR
                image = enhance_image_for_ocr(image)
                
                # Perform OCR
                config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?@#$%^&*()_+-=[]{}|;:\'"<>/\~$ '
                
                try:
                    page_text = pytesseract.image_to_string(image, config=config)
                    if page_text.strip():
                        extracted_text += page_text + "\n\n"
                        successful_pages += 1
                except Exception as ocr_error:
                    logger.warning(f"OCR failed for page {page_num}: {ocr_error}")
                    continue
                    
            except Exception as page_error:
                logger.warning(f"Failed to process page {page_num}: {page_error}")
                continue
        
        if successful_pages > 0:
            cleaned_text = clean_extracted_text(extracted_text)
            logger.info(f"OCR completed on {successful_pages}/{len(doc)} pages")
            return cleaned_text
        else:
            logger.warning("OCR failed on all pages")
            return None
            
    except Exception as e:
        logger.error(f"OCR extraction error: {e}")
        return None

def enhance_image_for_ocr(image):
    """Enhance image quality for better OCR."""
    try:
        from PIL import ImageEnhance, ImageFilter
        
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Enhance contrast
        contrast_enhancer = ImageEnhance.Contrast(image)
        image = contrast_enhancer.enhance(1.5)
        
        # Enhance sharpness
        sharpness_enhancer = ImageEnhance.Sharpness(image)
        image = sharpness_enhancer.enhance(1.2)
        
        # Reduce noise
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        return image
        
    except Exception as e:
        logger.warning(f"Image enhancement failed: {e}")
        return image

def clean_extracted_text(text: str) -> str:
    """Clean and normalize extracted text."""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Remove OCR artifacts
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'\|{2,}', '', text)
    text = re.sub(r'_{3,}', '', text)
    
    # Fix spacing
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    text = re.sub(r'([,.!?;:])\s*([A-Z])', r'\1 \2', text)
    
    # Fix common OCR substitutions
    text = re.sub(r'\b0(?=[A-Z])', 'O', text)
    text = re.sub(r'\b1(?=[A-Z])', 'I', text)
    
    return text.strip()

def is_meaningful_text(text: str) -> bool:
    """Check if text contains meaningful content."""
    if not text or len(text.strip()) < 30:
        return False
    
    # Calculate ratios
    letters = sum(c.isalpha() for c in text)
    digits = sum(c.isdigit() for c in text)
    total_alphanumeric = letters + digits
    total_chars = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
    
    if total_chars == 0:
        return False
    
    alphanumeric_ratio = total_alphanumeric / total_chars
    
    if alphanumeric_ratio < 0.4:
        return False
    
    # Check for tax keywords
    tax_keywords = [
        'irs', 'tax', 'notice', 'payment', 'due', 'amount', 'balance',
        'social security', 'ssn', 'form', 'return', 'refund', 'cp',
        'letter', 'department', 'treasury', 'internal revenue'
    ]
    
    text_lower = text.lower()
    keyword_found = any(keyword in text_lower for keyword in tax_keywords)
    
    if keyword_found and alphanumeric_ratio > 0.25:
        return True
    
    return alphanumeric_ratio > 0.4
