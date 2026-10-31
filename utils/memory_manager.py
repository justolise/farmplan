import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Handles stateful snapshots of the farm's current state to prevent context drift
    in long-running agentic conversations.
    """
    def __init__(self):
        self.snapshots: Dict[str, List[Dict[str, Any]]] = {}

    def create_snapshot(self, session_id: str, farm_profile: Dict[str, Any], last_logs: List[Any], current_phase: str) -> str:
        """
        Creates a compact summary of the farm's state.
        """
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "profile": farm_profile,
            "recent_activity_summary": f"Last 3 activities: {[str(l) for l in last_logs[-3:]]}",
            "phase": current_phase
        }

        if session_id not in self.snapshots:
            self.snapshots[session_id] = []

        self.snapshots[session_id].append(snapshot)

        # Return a human-readable string for the LLM context
        return (
            f"FARM STATE SNAPSHOT ({snapshot['timestamp']}):\n"
            f"- Phase: {current_phase}\n"
            f"- Profile: {farm_profile.get('soil_type', 'N/A')} soil, {farm_profile.get('main_crops', 'N/A')} crops\n"
            f"- Recent Status: {snapshot['recent_activity_summary']}"
        )

    def get_latest_snapshot(self, session_id: str) -> Optional[str]:
        if session_id not in self.snapshots or not self.snapshots[session_id]:
            return None

        last = self.snapshots[session_id][-1]
        return (
            f"LAST KNOWN STATE: Phase {last['phase']}, "
            f"Recent Activity: {last['recent_activity_summary']}"
        )

    def clear_session(self, session_id: str):
        if session_id in self.snapshots:
            del self.snapshots[session_id]

    def trim_history(self, history: List[Dict[str, Any]], max_messages: int = 10) -> List[Dict[str, Any]]:
        """Keep only the most recent N messages to prevent context overflow."""
        if not history or len(history) <= max_messages:
            return history
        return history[-max_messages:]

    def summarize_history(self, history: List[Dict[str, Any]], max_messages: int = 10) -> str:
        """Summarize conversation history prior to the active sliding window."""
        if not history or len(history) <= max_messages:
            return ""

        older_messages = history[:-max_messages]
        summary_points = []
        for msg in older_messages:
            role = msg.get("role", "unknown")
            content = str(msg.get("content", "")).strip()
            if len(content) > 120:
                content = content[:117] + "..."
            summary_points.append(f"{role.capitalize()}: {content}")

        return "Earlier context:\n" + "\n".join(summary_points)
