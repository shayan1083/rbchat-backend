from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage 
import traceback
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# custom classes and functions
from llm_logger import log_tool_start, log_tool_end, log_llm_usage, log_error
from settings import Settings
from db_memory import get_session_history, ensure_chat_history_table_exists
from prompts import sql_generation_template
from user_repository import UserRepository
# from file_upload import load_and_chunk_file


settings = Settings()

model = ChatOpenAI(model="gpt-4o", streaming=True, verbose=True, stream_usage=True)

async def run_agent(prompt: str, session_id: str = "default", file_context: dict = None):
    """Async generator for streaming agent responses to FastAPI"""
    try:
        ensure_chat_history_table_exists()
        async with streamablehttp_client(url=settings.MCP_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)

                with UserRepository() as repo:
                    schema_info = repo.get_tables_info()

                formatted_sql_prompt = sql_generation_template.format(
                    dialect=settings.DIALECT,
                    top_k=settings.TOP_K,
                    tables_info=schema_info
                )
                combined_prompt = formatted_sql_prompt
                if file_context:
                    combined_prompt += '\n\nAdditional file context provided by user:\n'
                    combined_prompt += f'File Name: {file_context["filename"]}\n' 
                    escaped_content = file_context['chunks'].replace("{", "{{").replace("}", "}}")
                    combined_prompt += f'File Content: \n\n{escaped_content}'

                # print(combined_prompt)

                agent_prompt = ChatPromptTemplate.from_messages([
                    ("system", combined_prompt),
                    MessagesPlaceholder(variable_name="messages")
                ])

                agent = create_react_agent(model, tools, prompt=agent_prompt)

                history = get_session_history(session_id)
                messages = history.messages[-settings.MEMORY_LIMIT:]
                messages.append(HumanMessage(content=prompt))

                full_response = ""
                input_tokens = None
                output_tokens = None
                total_tokens = None
                tool_name = None
                tool_input = None

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
                        tool_input = event["data"].get("input").get("query")
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
        log_error(f"LLM run_agent error: {traceback.format_exc()}")
        traceback.print_exc()

