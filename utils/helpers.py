from typing import Dict, List  # noqa: UP035

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def convert_history_to_messages(history: List[Dict[str, str]]) -> List[BaseMessage]:
    lc_messages = []
    for m in history:
        if m["role"] == "user":
            lc_messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            lc_messages.append(AIMessage(content=m["content"]))
    return lc_messages
