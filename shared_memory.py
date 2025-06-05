import json
import os
from datetime import datetime
from typing import Any, Dict

MEMORY_FILE = "shared_memory.json"

def load_memory() -> Dict[str, Any]:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_memory(memory: Dict[str, Any]):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memory, f, indent=2, default=str)

def log_agent_trace(entry: Dict[str, Any]):
    memory = load_memory()
    traces = memory.get('traces', [])
    traces.append(entry)
    memory['traces'] = traces
    save_memory(memory)

def log_agent_result(agent: str, input_meta: Dict[str, Any], extracted: Dict[str, Any], actions: list, trace: str):
    memory = load_memory()
    results = memory.get('results', [])
    results.append({
        'timestamp': datetime.now().isoformat(),
        'agent': agent,
        'input_meta': input_meta,
        'extracted': extracted,
        'actions': actions,
        'trace': trace
    })
    memory['results'] = results
    save_memory(memory)
