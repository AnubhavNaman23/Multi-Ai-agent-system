import re
from typing import Dict, Any

def parse_email(email_text):
    """
    Basic email parsing: remove headers, signatures, and clean text.
    """
    # For now, just return the raw text. Expand with real parsing as needed.
    return email_text.strip()

def extract_email_fields(email_text: str) -> Dict[str, Any]:
    """
    Improved extraction: sender, urgency, issue/request from email text.
    """
    sender = None
    urgency = 'routine'
    issue = None
    # Improved sender extraction (From: ... or first email in header)
    sender_match = re.search(r'^From:\s*(.*)$', email_text, re.MULTILINE | re.IGNORECASE)
    if not sender_match:
        # Try to find first email address in header
        sender_match = re.search(r'[\w\.-]+@[\w\.-]+', email_text)
    if sender_match:
        sender = sender_match.group(1) if sender_match.lastindex else sender_match.group(0)
        sender = sender.strip()
    # Improved urgency detection
    if re.search(r'urgent|asap|immediately|priority|demand immediate action', email_text, re.IGNORECASE):
        urgency = 'escalate'
    # Improved issue/request extraction: first non-header, non-empty line after Subject
    lines = email_text.splitlines()
    found_subject = False
    for line in lines:
        if found_subject and line.strip():
            issue = line.strip()
            break
        if re.match(r'^Subject:', line, re.IGNORECASE):
            found_subject = True
    # Fallback: look for complaint/issue keywords
    if not issue:
        for line in lines:
            if re.search(r'complain|issue|problem|dissatisfied|not acceptable', line, re.IGNORECASE):
                issue = line.strip()
                break
    return {'sender': sender, 'urgency': urgency, 'issue': issue}

def detect_tone(email_text: str) -> str:
    """
    Improved tone detection: escalation, polite, threatening, angry, neutral.
    """
    if re.search(r'not acceptable|legal action|threat|lawsuit|escalate|demand immediate action|extremely dissatisfied|angry', email_text, re.IGNORECASE):
        return 'escalation'
    if re.search(r'please|kindly|thank you|appreciate', email_text, re.IGNORECASE):
        return 'polite'
    if re.search(r'urgent|immediately|asap|priority', email_text, re.IGNORECASE):
        return 'escalation'
    return 'neutral'

def trigger_action(email_fields: Dict[str, Any], tone: str) -> str:
    """
    Triggers action based on tone and urgency.
    Escalate: notify CRM (simulate with API)
    Routine: log and close
    """
    if email_fields['urgency'] == 'escalate' or tone in ['escalation', 'threatening']:
        # Simulate CRM notification
        return f"[ACTION] Escalated: Notified CRM for sender {email_fields['sender']} (issue: {email_fields['issue']})"
    else:
        # Simulate logging and closing
        return f"[ACTION] Routine: Logged and closed for sender {email_fields['sender']} (issue: {email_fields['issue']})"
