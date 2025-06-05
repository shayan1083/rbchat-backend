from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage 
import traceback

# custom classes and functions
from llm_logger import log_tool_start, log_tool_end, log_llm_usage
from settings import Settings
from memory import get_session_history
from db_memory import get_session_history
from prompts import agent_prompt, raw_prompt


settings = Settings()

model = ChatOpenAI(model="gpt-4o", streaming=True, verbose=True, stream_usage=True)



async def run_agent(prompt: str, session_id: str = "default"):
    """Async generator for streaming agent responses to FastAPI"""
    try:
        async with streamablehttp_client(url=settings.MCP_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                agent = create_react_agent(model, tools, prompt=agent_prompt)

                history = get_session_history(session_id)
                messages = history.messages
                messages.append(HumanMessage(content=prompt))

                full_response = ""
                input_tokens = None
                output_tokens = None
                total_tokens = None
                tool_name = None

                async for event in agent.astream_events(
                    {"messages": messages},
                    version="v2"
                ):  
                    if event["event"] == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        usage = getattr(chunk, "usage_metadata", None)
                        if usage:
                            input_tokens = usage.get("input_tokens")
                            output_tokens = usage.get("output_tokens")
                            total_tokens = usage.get("total_tokens")
                        
                        if hasattr(chunk, "content") and chunk.content:
                            full_response += chunk.content
                            yield f"data: {chunk.content}\n\n"
                    
                    elif event["event"] == "on_tool_start":
                        tool_name = event["name"]
                        log_tool_start(tool_name)
                    
                    elif event["event"] == "on_tool_end":
                        log_tool_end(tool_name, output=event["data"].get("output", ""))
                history.add_message(HumanMessage(content=prompt))
                history.add_message(AIMessage(content=full_response))
                token_usage = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens
                }
                log_llm_usage(model.model_name, prompt, full_response, token_usage, tool_name)
                
    except Exception as e:
        print("Full traceback:")
        traceback.print_exc()


async def call_llm(prompt: str, session_id: str = "default"):
    """
    Streams a raw response from the LLM (no tools, no agent)
    """
    history = get_session_history(session_id)
    messages = history.messages
    messages.append(HumanMessage(content=prompt))

    formatted_messages = raw_prompt.format_messages(messages=messages) 
        
    full_response = ""
    input_tokens = None
    output_tokens = None
    total_tokens = None
    try:
        # stream response tokens directly
        async for chunk in model.astream(formatted_messages):
            usage = getattr(chunk, "usage_metadata", None)
            if usage:
                input_tokens = usage.get("input_tokens")
                output_tokens = usage.get("output_tokens")
                total_tokens = usage.get("total_tokens")
            full_response += chunk.content
            yield f"data: {chunk.content}\n\n"

        history.add_message(HumanMessage(content=prompt))
        history.add_message(AIMessage(content=full_response))

        token_usage = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens
        }
        log_llm_usage(model.model_name, prompt, full_response, token_usage)
    except Exception as e:
        print("Full traceback:")
        traceback.print_exc()
