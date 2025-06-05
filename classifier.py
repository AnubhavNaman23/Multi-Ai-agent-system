import re
from typing import Tuple

FEW_SHOT_EXAMPLES = [
    ("We are not satisfied with the product and want to complain.", "Complaint"),
    ("Please find attached the invoice for your recent purchase.", "Invoice"),
    ("As per the new regulation, you must update your policy.", "Regulation"),
    ("This is a request for quotation (RFQ) for your services.", "RFQ"),
    ("We detected a suspicious transaction that may indicate fraud.", "Fraud Risk"),
]

def classify_intent(email_text: str) -> Tuple[str, float]:
    """
    Classifies the intent of the input using few-shot examples and keyword/schema matching.
    Returns (intent, confidence).
    """
    patterns = {
        'Complaint': [r'not satisfied', r'complain', r'issue', r'problem', r'unsatisfactory'],
        'Invoice': [r'invoice', r'payment due', r'bill', r'amount due'],
        'Regulation': [r'compliance', r'regulation', r'policy', r'legal'],
        'Fraud Risk': [r'fraud', r'scam', r'suspicious', r'unauthorized', r'risk'],
        'RFQ': [r'request for quotation', r'rfq', r'quote', r'quotation'],
    }
    text = email_text.lower()
    
    for intent, pats in patterns.items():
        for pat in pats:
            if re.search(pat, text):
                return intent, 0.95
    
    for example, ex_intent in FEW_SHOT_EXAMPLES:
        if example.lower() in text:
            return ex_intent, 0.90
    return 'Unknown', 0.5
