import argparse
import os
import shutil
from format_detector import detect_format, extract_text

def upload_and_run(source_file_path):
    """
    Copies the given file to the uploads directory and runs the main pipeline on it.
    """
    uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    dest_file = os.path.join(uploads_dir, os.path.basename(source_file_path))
    shutil.copy2(source_file_path, dest_file)
    print(f"File uploaded to: {dest_file}")


    import sys
    sys.argv = [sys.argv[0], '--input_file', dest_file]

    main_pipeline()

def main_pipeline():
    parser = argparse.ArgumentParser(description="Multi-Format Classifier Agent")
    parser.add_argument('--input_file', type=str, required=False, help='Path to input file (Email, JSON, or PDF)')
    parser.add_argument('--email_text', type=str, required=False, help='Raw email text input (overrides input_file if provided)')
    args = parser.parse_args()

    if args.email_text:
        fmt = 'Email'
        input_text = args.email_text
    else:
        fmt = detect_format(args.input_file)
        print(f"Detected Format: {fmt}")
        input_text = extract_text(args.input_file, fmt)

    if fmt == 'Email':
        from email_parser import parse_email, extract_email_fields, detect_tone, trigger_action
        from shared_memory import log_agent_result
        from classifier import classify_intent
        parsed_text = parse_email(input_text)
        email_fields = extract_email_fields(input_text)
        tone = detect_tone(input_text)

        # Use classifier to get intent and confidence
        intent, confidence = classify_intent(parsed_text)
        action_result = trigger_action(email_fields, tone)
        print(f"Email Fields: {email_fields}")
        print(f"Detected Tone: {tone}")
        print(f"Detected Intent: {intent} (Confidence: {confidence:.2f})")
        print(action_result)

        # Log to shared memory
        log_agent_result(
            agent='EmailAgent',
            input_meta={'source': args.input_file, 'timestamp': None, 'format': fmt},
            extracted={**email_fields, 'tone': tone, 'intent': intent, 'confidence': confidence},
            actions=[action_result],
            trace=f"Fields: {email_fields}, Tone: {tone}, Intent: {intent}, Confidence: {confidence}, Action: {action_result}"
        )

        from action_router import route_action
        from retry_utils import retry_action
        routing_metadata = {
            'format': fmt,
            'intent': intent,
            'confidence': confidence,
            'file': os.path.basename(args.input_file) if args.input_file else 'user_input_email'
        }
        actions = [action_result]
        # Retry logic for action router
        triggered = retry_action(route_action, 3, 2, routing_metadata, actions)
        if triggered:
            print(f"Action Router triggered: {triggered}")
    else:
        parsed_text = input_text
        # JSON Agent logic
        if fmt == 'JSON':
            import json
            from format_detector import validate_json_schema, log_json_alert
            from shared_memory import log_agent_result
            data = json.loads(input_text)

            # Example required schema (customize as needed)
            required_fields = {
                'event': str,
                'timestamp': str,
                'payload': dict
            }
            is_valid, anomalies = validate_json_schema(data, required_fields)
            actions = []
            if not is_valid:
                log_json_alert(anomalies, data)
                actions.append(f"Alert: {anomalies}")
            else:
                print("JSON schema valid. No anomalies detected.")
                actions.append("Schema valid")

            # Log to shared memory
            log_agent_result(
                agent='JSONAgent',
                input_meta={'source': args.input_file, 'timestamp': data.get('timestamp'), 'format': fmt},
                extracted=data,
                actions=actions,
                trace=f"Anomalies: {anomalies}" if anomalies else "Schema valid"
            )

        # PDF Agent logic
        elif fmt == 'PDF':
            from format_detector import extract_pdf_invoice_fields, extract_pdf_policy_mentions, flag_pdf_alerts
            from shared_memory import log_agent_result
            pdf_fields = extract_pdf_invoice_fields(input_text)
            policy_mentions = extract_pdf_policy_mentions(input_text)
            flag_pdf_alerts(pdf_fields, policy_mentions)
            actions = []
            if pdf_fields.get('total') and pdf_fields['total'] > 10000:
                actions.append(f"Invoice total exceeds 10,000: {pdf_fields['total']}")
            if policy_mentions:
                actions.append(f"Policy mentions: {policy_mentions}")

            # Log to shared memory
            log_agent_result(
                agent='PDFAgent',
                input_meta={'source': args.input_file, 'timestamp': None, 'format': fmt},
                extracted={**pdf_fields, 'policy_mentions': policy_mentions},
                actions=actions,
                trace=f"Fields: {pdf_fields}, Policy: {policy_mentions}"
            )

    # Only run classifier for non-E2E Email path
    if not (fmt == 'Email'):
        from classifier import classify_intent
        intent, confidence = classify_intent(parsed_text)
        print(f"Detected Intent: {intent} (Confidence: {confidence:.2f})")
        routing_metadata = {
            'format': fmt,
            'intent': intent,
            'confidence': confidence,
            'file': os.path.basename(args.input_file) if args.input_file else 'user_input_email'
        }
        print(f"Routing Metadata: {routing_metadata}")
        from action_router import route_action
        actions = []
        if fmt == 'JSON':
            actions = actions 
        elif fmt == 'PDF':
            actions = actions  
        triggered = route_action(routing_metadata, actions)
        if triggered:
            print(f"Action Router triggered: {triggered}")

    # --- Print summary from shared memory ---
    from shared_memory import load_memory
    memory = load_memory()

    # Find the latest entry for this input
    input_id = args.input_file if args.input_file else 'user_input_email'
    latest_entry = None
    for entry in reversed(memory.get('results', [])):
        entry_id = entry['input_meta'].get('source') or 'user_input_email'
        if entry_id == input_id:
            latest_entry = entry
            break
    print("\n=== AGENT SUMMARY FOR THIS INPUT ===")
    if latest_entry:
        print(f"Timestamp: {latest_entry['timestamp']}")
        print(f"Agent: {latest_entry['agent']}")
        print(f"Input Source: {latest_entry['input_meta'].get('source')}")
        print(f"Input Format: {latest_entry['input_meta'].get('format')}")
        if latest_entry['input_meta'].get('timestamp'):
            print(f"Input Timestamp: {latest_entry['input_meta'].get('timestamp')}")
        print("\n--- Extracted Fields ---")
        for k, v in latest_entry['extracted'].items():

            # Add extra explanation for key business intents
            if k.lower() == 'intent' and v in ['RFQ', 'Complaint', 'Invoice', 'Regulation', 'Fraud Risk']:
                intent_desc = {
                    'RFQ': 'Request for Quotation: A request for pricing or proposal.',
                    'Complaint': 'Complaint: Expression of dissatisfaction or issue.',
                    'Invoice': 'Invoice: A request for payment for goods/services.',
                    'Regulation': 'Regulation: Reference to compliance or legal requirements.',
                    'Fraud Risk': 'Fraud Risk: Potentially suspicious or risky content.'
                }
                print(f"{k.capitalize()}: {v}  <-- {intent_desc[v]}")
            else:
                print(f"{k.capitalize()}: {v}")
        print("\n--- Actions Taken ---")
        for action in latest_entry['actions']:
            print(f"- {action}")
        print("\n--- Agent Trace ---")
        print(latest_entry['trace'])
        print("\n--- End of Entry ---")
    else:
        print("No summary found for this input.")
    print("\n=== END OF SUMMARY ===\n")

# Entry point logic
if __name__ == "__main__":
    import sys
    if '--upload_and_run' in sys.argv:
        idx = sys.argv.index('--upload_and_run')
        if idx + 1 < len(sys.argv):
            upload_and_run(sys.argv[idx + 1])
        else:
            print("Error: --upload_and_run requires a file path argument.")
    else:
        main_pipeline()
