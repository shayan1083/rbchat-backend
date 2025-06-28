install all requirements using pip:
- pip install -r requirements.txt

run mcp server:
- uvicorn tools:app --reload --port 7999

run mcp client:
- uvicorn main:app --reload --port 8003 

frontend in other git repo