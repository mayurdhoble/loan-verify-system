import pytesseract
import fitz  # PyMuPDF
import os

class OCRProcessor:
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF including embedded images"""
        try:
            import pdfplumber
            
            all_text = []
            
            # Direct text extraction
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text.append(text)
            
            # Extract from embedded images
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                images = page.get_images()
                
                for img_index, img in enumerate(images):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        temp_img = f"temp_{page_num}_{img_index}.png"
                        with open(temp_img, "wb") as f:
                            f.write(image_bytes)
                        
                        text = pytesseract.image_to_string(temp_img)
                        if text.strip():
                            all_text.append(text)
                        
                        if os.path.exists(temp_img):
                            os.remove(temp_img)
                    except:
                        pass
            
            doc.close()
            return '\n\n'.join(all_text)
            
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""