
# services/ocr.py
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import os
from docx import Document as DocxDocument
import csv
def extract_text_from_csv(path, doc_id=None):
    try:
        with open(path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows = [' | '.join(row) for row in reader if any(row)]
            text = '\n'.join(rows).strip()
            if text:
                return [{
                    'text': text,
                    'metadata': {
                        'doc_id': doc_id or os.path.basename(path),
                        'page': 1,
                        'paragraph': 1,
                        'source': path
                    }
                }]
    except Exception as e:
        print(f"Failed to read .csv file {path}: {e}")
    return []

def extract_text_from_docx(path, doc_id=None):
    try:
        doc = DocxDocument(path)
        text = '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
        if text:
            return [{
                'text': text,
                'metadata': {
                    'doc_id': doc_id or os.path.basename(path),
                    'page': 1,
                    'paragraph': 1,
                    'source': path
                }
            }]
    except Exception as e:
        print(f"Failed to read .docx file {path}: {e}")
    return []
def extract_text_from_pdf(path, doc_id=None):
    """Extract text from PDF with enhanced metadata"""
    text_chunks = []
    
    try:
        with pdfplumber.open(path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    # Split into paragraphs for better chunking
                    paragraphs = page_text.split('\n\n')
                    for para_num, paragraph in enumerate(paragraphs, 1):
                        if paragraph.strip():
                            text_chunks.append({
                                'text': paragraph.strip(),
                                'metadata': {
                                    'doc_id': doc_id or os.path.basename(path),
                                    'page': page_num,
                                    'paragraph': para_num,
                                    'source': path
                                }
                            })
    except Exception as e:
        print(f"pdfplumber failed for {path}, falling back to OCR:", e)
        # Fallback OCR
        try:
            images = convert_from_path(path)
            for page_num, image in enumerate(images, 1):
                ocr_text = pytesseract.image_to_string(image)
                if ocr_text.strip():
                    text_chunks.append({
                        'text': ocr_text.strip(),
                        'metadata': {
                            'doc_id': doc_id or os.path.basename(path),
                            'page': page_num,
                            'paragraph': 1,
                            'source': path,
                            'extracted_via': 'OCR'
                        }
                    })
        except Exception as ocr_error:
            print(f"OCR also failed for {path}: {ocr_error}")
    
    return text_chunks

def extract_text_from_image(path, doc_id=None):
    """Extract text from image using OCR"""
    try:
        image = Image.open(path)
        text = pytesseract.image_to_string(image)
        if text.strip():
            return [{
                'text': text.strip(),
                'metadata': {
                    'doc_id': doc_id or os.path.basename(path),
                    'page': 1,
                    'paragraph': 1,
                    'source': path,
                    'extracted_via': 'OCR'
                }
            }]
    except Exception as e:
        print(f"Failed to extract text from image {path}: {e}")
    
    return []
