import os
import json
import re
from typing import Tuple, Dict, Any
from PyPDF2 import PdfReader

def detect_format(input_path: str) -> str:
    """
    Detects the format of the input file: JSON, Email (txt), or PDF.
    """
    ext = os.path.splitext(input_path)[1].lower()
    if ext == '.json':
        return 'JSON'
    elif ext == '.pdf':
        return 'PDF'
    elif ext in ['.txt', '.eml']:
        return 'Email'
    else:
        # Try to infer from content
        with open(input_path, 'rb') as f:
            start = f.read(2048)
            if b'%PDF' in start:
                return 'PDF'
            try:
                json.loads(start.decode(errors='ignore'))
                return 'JSON'
            except Exception:
                return 'Email'

def extract_text(input_path: str, fmt: str) -> str:
    """
    Extracts text from the input file based on its format.
    """
    if fmt == 'JSON':
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Try to extract a main text field
        for key in ['body', 'text', 'content', 'message']:
            if key in data:
                return str(data[key])
        return json.dumps(data)
    elif fmt == 'PDF':
        reader = PdfReader(input_path)
        text = "\n".join(page.extract_text() or '' for page in reader.pages)
        return text
    else:  # Email or txt
        with open(input_path, 'r', encoding='utf-8') as f:
            return f.read()

def validate_json_schema(data: Dict[str, Any], required_fields: Dict[str, type]) -> Tuple[bool, list]:
    """
    Validates that all required fields exist and have the correct type.
    Returns (is_valid, list_of_anomalies)
    """
    anomalies = []
    for field, ftype in required_fields.items():
        if field not in data:
            anomalies.append(f"Missing field: {field}")
        elif not isinstance(data[field], ftype):
            anomalies.append(f"Type error: {field} should be {ftype.__name__}, got {type(data[field]).__name__}")
    return (len(anomalies) == 0, anomalies)

def log_json_alert(anomalies: list, data: Dict[str, Any]):
    """
    Simulate logging an alert for JSON anomalies (print or write to file/memory).
    """
    print(f"[ALERT] JSON Anomalies Detected: {anomalies}\nData: {json.dumps(data)[:200]}")

def extract_pdf_invoice_fields(text: str) -> Dict[str, Any]:
    """
    Extracts line-item and total from invoice PDF text.
    """
    # Simple regex for total (customize for real invoices)
    total_match = re.search(r'Total\s*[:\-]?\s*\$?([\d,]+\.?\d*)', text, re.IGNORECASE)
    total = float(total_match.group(1).replace(',', '')) if total_match else None
    # Extract line items (very basic: lines with qty, desc, price)
    line_items = re.findall(r'^(\d+)\s+([\w\s]+)\s+\$?([\d,]+\.?\d*)$', text, re.MULTILINE)
    items = [{'qty': int(q), 'desc': d.strip(), 'price': float(p.replace(',', ''))} for q, d, p in line_items]
    return {'total': total, 'line_items': items}

def extract_pdf_policy_mentions(text: str) -> list:
    """
    Flags if policy mentions GDPR, FDA, etc.
    """
    keywords = ['GDPR', 'FDA', 'HIPAA', 'SOX', 'PCI']
    mentions = [kw for kw in keywords if re.search(rf'\b{kw}\b', text, re.IGNORECASE)]
    return mentions

def flag_pdf_alerts(pdf_fields: Dict[str, Any], policy_mentions: list):
    """
    Print alerts for PDF agent based on extracted data.
    """
    if pdf_fields.get('total') and pdf_fields['total'] > 10000:
        print(f"[ALERT] Invoice total exceeds 10,000: {pdf_fields['total']}")
    if policy_mentions:
        print(f"[ALERT] Policy mentions detected: {policy_mentions}")
