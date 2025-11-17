from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

Base = declarative_base()
engine = create_engine(Config.DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

class User(Base):
    """User authentication"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Flask-Login integration
    @property
    def is_active(self):
        return True
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)

class Member(Base):
    """Member with 3 documents and profile URL"""
    __tablename__ = 'members'
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, unique=True, nullable=False)
    
    # Documents
    doc_dfr = Column(String(500))
    doc_pa = Column(String(500))
    doc_title = Column(String(500))
    
    # Profile URL
    profile_url = Column(String(1000))
    
    # Metadata
    uploaded_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class DocumentExtraction(Base):
    """Data extracted from 3 documents by Agent 1"""
    __tablename__ = 'document_extractions'
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, nullable=False)
    
    # Extracted fields
    applicant_name = Column(String(255))
    vin = Column(String(255))
    loan_amount = Column(String(255))
    routing_no = Column(String(255))
    account_no = Column(String(255))
    
    extraction_date = Column(DateTime, default=datetime.utcnow)

class WebExtraction(Base):
    """Data extracted from web profile by Agent 2"""
    __tablename__ = 'web_extractions'
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, nullable=False)
    profile_url = Column(String(1000))
    
    # Extracted fields
    applicant_name = Column(String(255))
    vin = Column(String(255))
    loan_amount = Column(String(255))
    routing_no = Column(String(255))
    account_no = Column(String(255))
    
    extraction_date = Column(DateTime, default=datetime.utcnow)

class Verification(Base):
    """Verification results by Agent 3"""
    __tablename__ = 'verifications'
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, nullable=False)
    user_id = Column(Integer)
    
    # Comparison results
    similarity_score = Column(Float)
    status = Column(String(50))  # Verified / Not Verified
    matched_fields = Column(JSON)
    mismatched_fields = Column(JSON)
    
    # References
    doc_extraction_id = Column(Integer)
    web_extraction_id = Column(Integer)
    
    verification_date = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    return Session()