import pdfplumber
# pyrefly: ignore [missing-import]
import PyPDF2
from docx import Document

def extract_pdf_text_and_pages(file_path) -> tuple:
    """
    Extracts text contents and counts pages from PDF files.
    Tries pdfplumber first, falling back to PyPDF2 upon failure or empty results.
    """
    text = []
    pages_count = 0
    
    # Primary parsing: pdfplumber
    try:
        with pdfplumber.open(file_path) as pdf:
            pages_count = len(pdf.pages)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        extracted = "\n".join(text).strip()
        if extracted:
            return extracted, pages_count
    except Exception:
        # Fail silently to trigger fallback
        pass

    # Fallback parsing: PyPDF2
    try:
        # Re-initialize lists
        text = []
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            pages_count = len(reader.pages)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        return "\n".join(text).strip(), max(pages_count, 1)
    except Exception:
        return "", 1


def extract_docx_text_and_pages(file_path) -> tuple:
    """
    Extracts text contents and counts pages from Word (.docx) files.
    Calculates page counts by inspecting rendering break tags in the doc XML structure.
    """
    try:
        doc = Document(file_path)
        text = []
        
        # Extract from normal paragraphs
        for para in doc.paragraphs:
            if para.text:
                text.append(para.text)
                
        # Extract from tables structures
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text:
                        text.append(cell.text)
                        
        # Estimate page count by counting standard page breaks in document XML
        doc_xml = doc.element.xml
        xml_page_breaks = doc_xml.count('w:br w:type="page"')
        xml_rendered_breaks = doc_xml.count('w:lastRenderedPageBreak')
        
        pages_count = xml_page_breaks + xml_rendered_breaks + 1
        
        return "\n".join(text).strip(), max(pages_count, 1)
    except Exception:
        return "", 1


def parse_resume_document(file_path, file_type: str) -> tuple:
    """
    Router utility to parse document text and count pages based on file extension type.
    """
    ft = file_type.lower().strip('.')
    if ft == 'pdf':
        return extract_pdf_text_and_pages(file_path)
    elif ft in ['doc', 'docx']:
        return extract_docx_text_and_pages(file_path)
    return "", 1
