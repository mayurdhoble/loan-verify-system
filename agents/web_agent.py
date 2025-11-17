from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from bs4 import BeautifulSoup
from config import Config
import requests
import json

class WebAgent:
    """Agent 2: Extract data from web profile"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=Config.GEMINI_MODEL,
            google_api_key=Config.GOOGLE_API_KEY,
            temperature=0.1
        )
        
        template = """
        Extract loan information from this web profile:
        
        {html}
        
        Extract these fields (return "NOT_FOUND" if missing):
        - applicant_name: Full name
        - vin: Vehicle ID
        - loan_amount: Loan amount
        - routing_no: Routing number
        - account_no: Account number
        
        Return ONLY valid JSON with these keys.
        """
        
        self.prompt = PromptTemplate(template=template, input_variables=["html"])
    
    def process(self, url):
        """Scrape and extract from URL"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return {}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            llm_response = self.llm.invoke(self.prompt.format(html=response.text[:5000]))
            response_text = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
            
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
            print(f"Web extraction error: {e}")
        
        return {}