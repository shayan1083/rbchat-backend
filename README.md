install all requirements using pip:
- pip install -r requirements.txt

run db_memory to create chat history table:
currently commented out so uncomment create_tables text first
- python db_memory.py

run mcp server:
- python tools.py

run mcp client:
- uvicorn main:app --reload --port 8003 

frontend in other git repo