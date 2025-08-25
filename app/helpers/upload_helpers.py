import io
import pdfplumber
from docx import Document

def extract_text_from_pdf(file_stream):
    try:
        with pdfplumber.open(file_stream) as pdf:
            text = "\n".join(page.extract_text() or '' for page in pdf.pages)
        return text.strip()
    except Exception as e:
        print(" PDF parsing error:", str(e))
        return ""

def extract_text_from_docx(file_stream):
    try:
        doc = Document(file_stream)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text.strip()
    except Exception as e:
        print("DOCX parsing error:", str(e))
        return ""

def is_resume_parsable(file_stream, filename):
    extension = filename.lower().split('.')[-1]
    
    file_stream.seek(0)  # Reset stream position before parsing

    if extension == 'pdf':
        text = extract_text_from_pdf(file_stream)
    elif extension == 'docx':
        text = extract_text_from_docx(file_stream)
    else:
        print("Unsupported file type")
        return False

    return bool(text and len(text) > 50)  # optional length check
