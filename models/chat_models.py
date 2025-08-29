from pydantic import BaseModel

class QueryRequest(BaseModel):
    prompt: str
    session_id: str
    db_name: str