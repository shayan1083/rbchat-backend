from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json
from llm_logger import log_tool_start, log_tool_end, log_llm_usage
import traceback
from settings import Settings


settings = Settings()

model = ChatOpenAI(model="gpt-4o", streaming=True, verbose=True, stream_usage=True)

                           
agent_template = """
            Act as helpful assistant that is able to get information from a database based on the users natural language query.
            You cannot answer questions that are not related to querying the database. If someone asks a question unrelated to your task, then say you cannot answer that due to my task.
            The retrieved context shall be provided by one of the registered tools.
            Pick the right tool to populate the context before giving the final answer to the given question.
            
            
            Tool calling instructions:
            
            1. Don't make any assumptions about the given question before retrieving the context. If the given question contains abbreviations or unknown words, don't try to interpret them before invoking one of the tools.

            2. If the tool returns a list of items, format the list using markdown. Start the list with \\n\\n, and put each item on its own line using \\n. For example:

            \n\n- **Item A**: Description ($Price)\n- **Item B**: Description ($Price)

            Do not say anything else before or after the list.

            3. When listing items, only list the items and anyting else the tool returns, say nothing else. Do not say something like "Here are the items:"

            4. If the tool returns a list of items, and the number of items to be retrieved is not specified by the user, use the default value of 10.

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
        async with streamablehttp_client(url=settings.MCP_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                agent = create_react_agent(model, tools, prompt=agent_prompt)

                full_response = ""
                input_tokens = None
                output_tokens = None
                total_tokens = None
                tool_name = None

                async for event in agent.astream_events(
                    {"messages": [{"role": "user", "content": prompt}]},
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
                token_usage = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens
                }
                log_llm_usage(model.model_name, prompt, full_response, token_usage, tool_name)
                
    except Exception as e:
        print(f"Error in run_agent: {e}")
        print("Full traceback:")
        traceback.print_exc()
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
    full_response = ""
    try:
        # stream response tokens directly
        async for chunk in model.astream(messages):
            usage = getattr(chunk, "usage_metadata", None)
            if usage:
                input_tokens = usage.get("input_tokens")
                output_tokens = usage.get("output_tokens")
                total_tokens = usage.get("total_tokens")
            full_response += chunk.content
            yield f"data: {chunk.content}\n\n"
        token_usage = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens
        }
        log_llm_usage(model.model_name, prompt, full_response, token_usage)
    except Exception as e:
        print(f"LLM stream error: {e}")
        yield f"data: Error: {e}\n\n"