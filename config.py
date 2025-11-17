import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Use environment variable for secret key in production
    SECRET_KEY = os.getenv('SECRET_KEY', 'loan-verify-secret-key-2025')
    
    # Dynamic paths for PythonAnywhere
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    DATA_FOLDER = os.path.join(BASE_DIR, 'data')
    
    # Database with absolute path
    DATABASE_URL = f'sqlite:///{os.path.join(DATA_FOLDER, "loan_verify.db")}'
    
    # API Configuration
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyBypcZBQt6JV4ohaKbalGa2E-gwSFXuvd4')
    GEMINI_MODEL = 'gemini-2.5-flash'
    
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB