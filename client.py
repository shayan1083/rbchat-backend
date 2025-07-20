from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage 
from langchain_core.rate_limiters import InMemoryRateLimiter
import traceback
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import openai
import json

from llm_logger import LLMLogger
from settings import Settings
from db_memory import get_session_history
from prompts import sql_generation_template
from user_repository import UserRepository
from file_upload import get_uploaded_data


settings = Settings()

logger = LLMLogger()

rate_limiter = InMemoryRateLimiter(
    requests_per_second=2,  
    check_every_n_seconds=0.1, 
    max_bucket_size=10,  
)

model = ChatOpenAI(model="gpt-4o", streaming=True, verbose=True, stream_usage=True)
     
async def run_agent(prompt: str, session_id: str = "default", db_name: str = settings.DB_NAME):   
    try:
        logger.info(f"Using LLM Model: {model.model_name}")
        logger.info(f"User Prompt: {prompt}")
        start_time = time.perf_counter()
        async with streamablehttp_client(url=settings.MCP_SERVER_URL,headers={'db_name':db_name}) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tools = await load_mcp_tools(session)  

                file_context = get_uploaded_data(session_id)
                agent_prompt = create_prompt(db_name, file_context)
                agent = create_react_agent(model, tools, prompt=agent_prompt)

                history = get_session_history(session_id)
                messages = history.messages[-settings.MEMORY_LIMIT:]
                messages.append(HumanMessage(content=prompt))

                full_response = ""
                input_tokens = None
                output_tokens = None
                total_tokens = None
                tool_name = None

                async for event in agent.astream_events({"messages": messages}, version="v2"):  
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
                    # elif event["event"] == "on_chat_model_start":
                    #     logger.info(f"Model started") 
                    #     yield f"event: modelstart\ndata: {json.dumps({'message': 'model started'})}\n\n"
                    elif event["event"] == "on_tool_start":
                        tool_name = event["name"]
                        logger.info(f"Tool Used: {tool_name}") 

                logger.log_on_chat_end(
                    history, prompt, full_response, start_time, input_tokens, output_tokens, total_tokens, model, tool_name
                )
                yield f"event: end\ndata: {json.dumps({'message': 'stream complete'})}\n\n"
                logger.info("[END] Process Finished")

    except Exception as e:
        logger.error(f"run_agent error: {traceback.format_exc()}")
        message = find_ratelimit_error(e)
        if message is not None:
            print(message)
            yield f"event: error\ndata: {json.dumps({'message': message})}\n\n"
        else:
            yield f"event: error\ndata: {json.dumps({'message': 'It seems there was an error. Please try again later.'})}\n\n"

def find_ratelimit_error(exc):
    while exc:
        if isinstance(exc, openai.RateLimitError):
            return exc
        exc = exc.__cause__ or exc.__context__
    return None



def create_prompt(db_name: str, file_context: dict = None):
    """Format and update the agent prompt with table schema and file content"""
    with UserRepository(dbname=db_name) as repo:
        schema_info = repo.get_tables_info()

    formatted_sql_prompt = sql_generation_template.format(
        dialect=settings.DIALECT,
        top_k=settings.TOP_K,
        tables_info=schema_info,
        export_k=settings.EXPORT_TOP_K,
        newline=settings.NEWLINE_CHAR
    )
    combined_prompt = formatted_sql_prompt
    if file_context:
        if isinstance(file_context['data'], list):
        # Convert list of dicts to a CSV-like string
            formatted_data = json.dumps(file_context['data'], indent=2)
        elif isinstance(file_context['data'], str):
            # Already a string, like from a .txt file
            formatted_data = file_context['data']
        else:
            # Fallback for unexpected data types
            formatted_data = json.dumps(file_context['data'], indent=2)

        # Escape braces for prompt injection safety
        escaped_content = formatted_data.replace("{", "{{").replace("}", "}}")
        
        combined_prompt += '\n\nAdditional file context provided by user:\n'
        combined_prompt += f'File Name: {file_context["filename"]}\n' 
        escaped_content = file_context['data'].replace("{", "{{").replace("}", "}}")
        combined_prompt += f'File Content: \n\n{escaped_content}'

    agent_prompt = ChatPromptTemplate.from_messages([
        ("system", combined_prompt),
        MessagesPlaceholder(variable_name="messages")
    ])

    return agent_prompt
