# gemini_api.py - Gemini API Integration Module
import os
import requests
import json
import logging
import time
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

def call_gemini_api(text: str, max_retries: int = 3) -> Optional[str]:
    """Call Gemini API to analyze tax notice text."""
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set")
        return None
    
    if not text or len(text.strip()) < 50:
        logger.error("Insufficient text for analysis")
        return None
    
    prompt = create_analysis_prompt(text)
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192,
        },
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    }
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Calling Gemini API (attempt {attempt + 1}/{max_retries})")
            
            response = requests.post(
                GEMINI_API_URL,
                json=payload,
                timeout=60,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract generated text
            if ('candidates' in result and 
                len(result['candidates']) > 0 and 
                'content' in result['candidates'][0] and 
                'parts' in result['candidates'][0]['content'] and 
                len(result['candidates'][0]['content']['parts']) > 0):
                
                generated_text = result['candidates'][0]['content']['parts'][0]['text']
                cleaned_response = clean_api_response(generated_text)
                
                # Validate JSON
                try:
                    json.loads(cleaned_response)
                    logger.info("Valid JSON received from Gemini API")
                    return cleaned_response
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON on attempt {attempt + 1}")
                    if attempt == max_retries - 1:
                        # Try to fix JSON
                        fixed_json = fix_common_json_issues(cleaned_response)
                        try:
                            json.loads(fixed_json)
                            return fixed_json
                        except json.JSONDecodeError:
                            logger.error("Could not fix JSON response")
                            return create_fallback_response(text)
            else:
                logger.error(f"Unexpected API response: {result}")
                
        except requests.exceptions.Timeout:
            logger.error(f"API timeout on attempt {attempt + 1}")
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed on attempt {attempt + 1}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
        
            # Exponential backoff
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt
            logger.info(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
    
    logger.error("All API attempts failed")
    return create_fallback_response(text)

def create_analysis_prompt(text: str) -> str:
    """Create comprehensive prompt for tax notice analysis."""
    return f"""
You are an expert tax notice analyst. Analyze the following text from a tax notice and extract information into a properly formatted JSON object.

CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON - no explanations or markdown
2. If information cannot be found, use empty string ""
3. Be precise with amounts - include dollar signs and exact formatting
4. For dates, use exact format found in document
5. All field names must match exactly as specified

Required JSON structure:
{{
  "noticeType": "The specific notice code (e.g., 'CP23', 'CP503C')",
  "noticeFor": "Full taxpayer name exactly as shown",
  "address": "Complete taxpayer address with \\n for line breaks",
  "ssn": "Social Security Number as shown (usually masked)",
  "amountDue": "Total amount due with dollar sign (e.g., '$1,234.56')",
  "payBy": "Payment due date exactly as written",
  "breakdown": [
    {{"item": "Description of charge/credit", "amount": "Amount with dollar sign"}},
    {{"item": "Description of charge/credit", "amount": "Amount with dollar sign"}}
  ],
  "noticeMeaning": "Concise 2-sentence explanation of what this notice type means",
  "whyText": "Detailed paragraph explaining why taxpayer received this notice",
  "fixSteps": {{
    "agree": "Step-by-step instructions if taxpayer agrees with notice",
    "disagree": "Step-by-step instructions if taxpayer disagrees with notice"
  }},
  "paymentOptions": {{
    "online": "Online payment URL or instructions",
    "mail": "Mailing instructions for payments",
    "plan": "Payment plan setup instructions or URL"
  }},
  "helpInfo": {{
    "contact": "Primary contact phone number for questions",
    "advocate": "Taxpayer Advocate Service information and contact details"
  }}
}}

Document text to analyze:
---
{text}
---

Return only the JSON object:"""

def clean_api_response(response_text: str) -> str:
    """Clean API response by removing markdown formatting."""
    # Remove markdown code blocks
    if response_text.strip().startswith("```json"):
        response_text = response_text.strip()[7:]
    if response_text.strip().startswith("```"):
        response_text = response_text.strip()[3:]
    if response_text.strip().endswith("```"):
        response_text = response_text.strip()[:-3]
    
    # Find JSON boundaries
    lines = response_text.split('\n')
    json_start = -1
    json_end = -1
    
    for i, line in enumerate(lines):
        if line.strip().startswith('{'):
            json_start = i
            break
    
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().endswith('}'):
            json_end = i
            break
    
    if json_start >= 0 and json_end >= 0:
        response_text = '\n'.join(lines[json_start:json_end + 1])
    
    return response_text.strip()

def fix_common_json_issues(json_string: str) -> str:
    """Attempt to fix common JSON formatting issues."""
    # Fix escape sequences
    json_string = json_string.replace('\n', '\\n')
    json_string = json_string.replace('\t', '\\t')
    json_string = json_string.replace('\r', '\\r')
    
    # Fix unescaped quotes
    json_string = re.sub(r'(?<!\\)"(?=[^,}])', '\\"', json_string)
    
    # Fix trailing commas
    json_string = re.sub(r',(\s*[}\]])', r'\1', json_string)
    
    # Fix missing commas
    json_string = re.sub(r'}\s*{', '},{', json_string)
    
    return json_string

def validate_analysis_result(json_string: str) -> bool:
    """Validate that analysis result contains required fields."""
    try:
        data = json.loads(json_string)
        
        required_fields = [
            'noticeType', 'noticeFor', 'address', 'ssn', 'amountDue',
            'payBy', 'breakdown', 'noticeMeaning', 'whyText', 'fixSteps',
            'paymentOptions', 'helpInfo'
        ]
        
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate nested objects
        if not isinstance(data.get('breakdown'), list):
            logger.warning("breakdown should be a list")
            return False
        
        nested_objects = ['fixSteps', 'paymentOptions', 'helpInfo']
        for obj_name in nested_objects:
            if not isinstance(data.get(obj_name), dict):
                logger.warning(f"{obj_name} should be an object")
                return False
        
        return True
        
    except json.JSONDecodeError as e:
        logger.warning(f"JSON validation failed: {e}")
        return False

def create_fallback_response(text: str) -> str:
    """Create basic fallback response when API fails."""
    # Extract basic information using regex
    notice_type = ""
    amount_due = ""
    
    # Common notice patterns
    cp_match = re.search(r'(CP\d+[A-Z]*)', text, re.IGNORECASE)
    if cp_match:
        notice_type = cp_match.group(1).upper()
    
    letter_match = re.search(r'(Letter \d+[A-Z]*)', text, re.IGNORECASE)
    if letter_match:
        notice_type = letter_match.group(1)
    
    # Amount patterns
    amount_match = re.search(r'\$[\d,]+\.?\d*', text)
    if amount_match:
        amount_due = amount_match.group(0)
    
    fallback_data = {
        "noticeType": notice_type,
        "noticeFor": "",
        "address": "",
        "ssn": "",
        "amountDue": amount_due,
        "payBy": "",
        "breakdown": [],
        "noticeMeaning": "This appears to be a tax notice requiring your attention.",
        "whyText": "Unable to determine specific reason. Please review the document carefully.",
        "fixSteps": {
            "agree": "Contact the IRS at the number provided to arrange payment.",
            "disagree": "Contact the IRS to dispute the notice or request additional information."
        },
        "paymentOptions": {
            "online": "www.irs.gov/payments",
            "mail": "Check the notice for mailing instructions",
            "plan": "www.irs.gov/paymentplan"
        },
        "helpInfo": {
            "contact": "Check the notice for specific contact information",
            "advocate": "Taxpayer Advocate Service: 1-877-777-4778"
        }
    }
    
    return json.dumps(fallback_data, indent=2)
