from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
import uvicorn
import os
import shutil
from main import detect_format, extract_text
from classifier import classify_intent
from email_parser import parse_email, extract_email_fields, detect_tone, trigger_action
from format_detector import validate_json_schema, log_json_alert, extract_pdf_invoice_fields, extract_pdf_policy_mentions, flag_pdf_alerts
from shared_memory import load_memory
from action_router import route_action

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/classify")
async def classify_file(file: UploadFile = File(...)):
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    fmt = detect_format(file_path)
    input_text = extract_text(file_path, fmt)
    result = {"format": fmt}
    actions = []
    routing_metadata = {}
    if fmt == 'Email':
        parsed_text = parse_email(input_text)
        email_fields = extract_email_fields(input_text)
        tone = detect_tone(input_text)
        action_result = trigger_action(email_fields, tone)
        intent, confidence = classify_intent(parsed_text)
        actions = [action_result]
        routing_metadata = {
            'format': fmt,
            'intent': intent,
            'confidence': confidence,
            'file': file.filename
        }
        
        # Route action
        triggered = route_action(routing_metadata, actions)
        result.update({
            "intent": intent,
            "confidence": confidence,
            "fields": email_fields,
            "tone": tone,
            "action": action_result,
            "router": triggered
        })
    elif fmt == 'JSON':
        import json
        data = json.loads(input_text)
        required_fields = {'event': str, 'timestamp': str, 'payload': dict}
        is_valid, anomalies = validate_json_schema(data, required_fields)
        intent, confidence = classify_intent(input_text)
        actions = []
        if not is_valid:
            actions.append(f"Alert: {anomalies}")
        else:
            actions.append("Schema valid")
        routing_metadata = {
            'format': fmt,
            'intent': intent,
            'confidence': confidence,
            'file': file.filename
        }
        triggered = route_action(routing_metadata, actions)
        result.update({
            "intent": intent,
            "confidence": confidence,
            "fields": data,
            "anomalies": anomalies,
            "schema_valid": is_valid,
            "router": triggered
        })
    elif fmt == 'PDF':
        pdf_fields = extract_pdf_invoice_fields(input_text)
        policy_mentions = extract_pdf_policy_mentions(input_text)
        intent, confidence = classify_intent(input_text)
        actions = []
        if pdf_fields.get('total') and pdf_fields['total'] > 10000:
            actions.append(f"Invoice total exceeds 10,000: {pdf_fields['total']}")
        if policy_mentions:
            actions.append(f"Policy mentions: {policy_mentions}")
        routing_metadata = {
            'format': fmt,
            'intent': intent,
            'confidence': confidence,
            'file': file.filename
        }
        triggered = route_action(routing_metadata, actions)
        result.update({
            "intent": intent,
            "confidence": confidence,
            "fields": pdf_fields,
            "policy_mentions": policy_mentions,
            "router": triggered
        })
    return JSONResponse(result)

@app.get("/memory")
def get_memory():
    memory = load_memory()
    return JSONResponse(memory)

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
