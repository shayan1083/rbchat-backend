from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from pathlib import Path
import json

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

api_key = os.getenv("OPENAI_API_KEY")

model = ChatOpenAI(model="gpt-4o", streaming=True, verbose=True)

server_params = StdioServerParameters(
    command="python",
    args=["app/tools.py"],
)

agent_template = """
            Act as helpful assistant and answer the given question.
            The retrieved context shall be provided by one of the registered tools.
            Pick the right tool to populate the context before giving the final answer to the given question.
            
            Tool calling instructions:
            
            1. Don't make any assumptions about the given question before retrieving the context. If the given question contains abbreviations or unknown words, don't try to interpret them before invoking one of the tools.

            2. If the tool returns a list of items, return it as a markup list

            3. If the tool returns a list of items, and the number of items to be retrieved is not specified by the user, use the default value of 10.

            Question answering instructions (after invoking the tool and retrieving the context):
            
            1. Provide your final answer based on the information in the retrieved context
            
            2. Don't make any assumptions about the given question before answering.
            If the given question contains abbreviations or unknown words which can be ambiguously interpreted ask user to clarify the question.
            
            3. If you don't know the answer just say that you don't know.
            
            4. Use only the data from the retrieved context to answer, don't make up.
            
            5. While answering don't mention context and context word explicitly, just provide answer to the question using the retrieved context transparently. 
            Don't use phrases like "Based on the context", "Based on the information available in the retrieved context" and similar.
 
        """

agent_prompt = ChatPromptTemplate.from_messages([
    ("system", agent_template),
    MessagesPlaceholder(variable_name="messages")
])

async def run_agent(prompt: str):
    """Async generator for streaming agent responses to FastAPI"""
    try:
        print(f"User prompt: {prompt}")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                agent = create_react_agent(model, tools, prompt=agent_prompt)

                full_response = ""
                total_tokens = 0

                # Use astream_events for finer-grained streaming
                async for event in agent.astream_events(
                    {"messages": [{"role": "user", "content": prompt}]},
                    version="v2"
                ):
                    #print(event)
                    # Handle different event types
                    if event["event"] == "on_chat_model_stream":
                        # Stream individual tokens from the LLM
                        chunk = event["data"]["chunk"]
                        if hasattr(chunk, "content") and chunk.content:
                            # yield f"data: {json.dumps({'content': chunk.content, 'type': 'token'})}\n\n"
                            full_response += chunk.content
                            yield f"data: {chunk.content}\n\n"
                            if "response_metadata" in chunk and "token_usage" in chunk.response_metadata:
                                total_tokens = chunk.response_metadata["token_usage"]["total_tokens"]
                    
                    elif event["event"] == "on_tool_start":
                        # Notify when tool execution starts
                        tool_name = event["name"]
                        print(f"🔧 Tool started: {tool_name}")
                        #yield f"data: {json.dumps({'content': f'🔧 Using tool: {tool_name}...', 'type': 'tool_start'})}\n\n"
                    
                    elif event["event"] == "on_tool_end":
                        # Notify when tool execution completes
                        tool_name = event["name"]
                        print(f"✅ Tool completed: {tool_name}")
                        if "output" in event["data"]:
                            print(f"🟡 Tool output: {event['data']['output']}")
                        #yield f"data: {json.dumps({'content': f'✅ Tool {tool_name} completed', 'type': 'tool_end'})}\n\n"
                print(f"💬 LLM final response: {full_response}")
                print(f"🧮 Tokens used: {total_tokens}\n")
                # Send completion signal
                #yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                
    except Exception as e:
        print(f"Error in run_agent: {e}")  # Server-side logging
        yield f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"



raw_template = """
            You are a helpful assistant. Answer the question using your own knowledge.
            If the users question requires some additional context, like a database call 
            or an API request, say that you don't know because you don't have access to that information.
                """


raw_prompt = ChatPromptTemplate.from_messages([
    ("system", raw_template),
    ("user", "{input}")
])


async def call_llm(prompt: str):
    """
    Streams a raw response from the LLM (no tools, no agent)
    """
    messages = raw_prompt.format_messages(input=prompt)
    try:
        # stream response tokens directly
        async for chunk in model.astream(messages):
            yield f"data: {chunk.content}\n\n"
    except Exception as e:
        print(f"LLM stream error: {e}")
        yield f"data: Error: {e}\n\n"