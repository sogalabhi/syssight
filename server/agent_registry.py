# server/agent_registry.py
from typing import Dict

# Agent registry: maps hostname -> "ip:port"
agent_registry: Dict[str, str] = {}
