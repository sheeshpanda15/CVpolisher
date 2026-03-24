import os

def extract_text(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.tex':
        with open(filepath, "r", encoding="utf8") as f:
            return f.read()
            
    elif ext == '.pdf':
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            return "错误：未安装 pdfplumber 库"
            
    elif ext == '.docx':
        try:
            import docx
            doc = docx.Document(filepath)
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            return "错误：未安装 python-docx 库"
            
    return ""