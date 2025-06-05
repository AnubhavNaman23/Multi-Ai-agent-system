import requests

def route_action(routing_metadata, agent_actions):
    """
    Simulate routing follow-up actions based on agent outputs.
    Triggers REST calls (simulated) for CRM, risk, compliance, etc.
    """
    actions_triggered = []
    
    if routing_metadata['format'] == 'Email':
        for action in agent_actions:
            if 'Escalated' in action or (routing_metadata.get('intent') == 'Complaint' and 'angry' in action.lower()):
            
                print('[ROUTER] POST /crm/escalate (simulated)')
                actions_triggered.append('POST /crm/escalate')
            elif 'Routine' in action:
                print('[ROUTER] No external action needed (routine)')

    # PDF: flag risk or compliance
    if routing_metadata['format'] == 'PDF':
        for action in agent_actions:
            if 'exceeds 10,000' in action:
                print('[ROUTER] POST /risk_alert (simulated)')
                actions_triggered.append('POST /risk_alert')
            if 'Policy mentions' in action:
                print('[ROUTER] POST /compliance_flag (simulated)')
                actions_triggered.append('POST /compliance_flag')

    # JSON: alert for anomalies
    if routing_metadata['format'] == 'JSON':
        for action in agent_actions:
            if 'Alert:' in action:
                print('[ROUTER] POST /json_alert (simulated)')
                actions_triggered.append('POST /json_alert')
    return actions_triggered
