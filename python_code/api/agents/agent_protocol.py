from typing import Protocol, List, Dict, Any

class AgentProtocol(Protocol):
    async def get_response(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        ...