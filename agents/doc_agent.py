from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from utils.ocr import OCRProcessor
from config import Config
import json

class DocumentAgent:
    """Agent 1: Extract data from 3 documents"""
    
    def __init__(self):
        self.ocr = OCRProcessor()
        self.llm = ChatGoogleGenerativeAI(
            model=Config.GEMINI_MODEL,
            google_api_key=Config.GOOGLE_API_KEY,
            temperature=0.1
        )
        
        template = """
        Extract loan information from these documents:
        
        {text}
        
        Extract these fields (return "NOT_FOUND" if missing):
        - applicant_name: Full name
        - vin: Vehicle ID (17 chars)
        - loan_amount: Loan amount
        - routing_no: Routing number (9 digits)
        - account_no: Account number
        
        Return ONLY valid JSON with these keys.
        """
        
        self.prompt = PromptTemplate(template=template, input_variables=["text"])
    
    def process(self, file_paths):
        """Extract from 3 PDFs"""
        all_text = []
        
        for path in file_paths:
            text = self.ocr.extract_text_from_pdf(path)
            if text:
                all_text.append(text)
        
        combined_text = '\n\n=== DOCUMENT ===\n\n'.join(all_text)
        
        try:
            response = self.llm.invoke(self.prompt.format(text=combined_text[:5000]))
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                data = json.loads(response_text[json_start:json_end])
                
                cleaned = {}
                for key, value in data.items():
                    if value and value != 'NOT_FOUND':
                        cleaned[key] = str(value).strip()
                
                return cleaned
        except Exception as e:
            print(f"Document extraction error: {e}")
        
        return {}