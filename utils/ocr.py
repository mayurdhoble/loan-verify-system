import fitz  # PyMuPDF

class OCRProcessor:
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF using PyMuPDF only (for text-based PDFs)"""
        try:
            all_text = []
            
            # Open PDF with PyMuPDF
            doc = fitz.open(pdf_path)
            
            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                if text and text.strip():
                    all_text.append(text)
            
            doc.close()
            
            # Combine all pages
            combined_text = '\n\n'.join(all_text)
            return combined_text
            
        except Exception as e:
            print(f"PDF Extraction Error: {e}")
            return ""
