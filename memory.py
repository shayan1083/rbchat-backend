from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from pydantic import BaseModel

class InMemoryHistory(BaseChatMessageHistory, BaseModel):
    messages: list[dict] = []
    
    def add_messages(self, messages: list[dict]):
        self.messages.extend(messages)
    
    def clear(self):
        self.messages = []

store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryHistory()
    return store[session_id]

def with_history(agent_runnable):
    return RunnableWithMessageHistory(
        agent_runnable,
        get_session_history=get_session_history,
        input_messages_key="messages",
        history_messages_key="messages",
        output_messages_key="output"
    )