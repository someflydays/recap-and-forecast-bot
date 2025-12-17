import os
import json
from dotenv import load_dotenv
from datetime import datetime
from typing_extensions import TypedDict
from typing import Annotated
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    AnyMessage,
)
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph_sdk import get_client
from pydantic import BaseModel


# Load API keys from recap-and-forecast-bot/backend/.env
load_dotenv()
GRAPH_KEY = os.getenv("LANGSMITH_API_KEY")
GRAPH_URL = os.getenv("LANGSMITH_API_URL", "http://localhost:8001")


# Instantiate FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define API request schema, validated with Pydantic
class ChatRequest(BaseModel):
    message: str
    mode: str  # "recap", "forecast", or "general"
    timeframe: str  # "today", "this week", ...
    model: str = "gpt-4o"  # "gpt-4o" or "gpt-5.2-2025-12-11"


# Define API response schema, validated with Pydantic
class ChatResponse(BaseModel):
    response: str


# Define graph state schema
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    mode: str
    timeframe: str
    topic: str
    model: str


# Create a function to load prompts from JSON files
THIS_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(THIS_DIR, ".."))
PROMPT_DIR = os.path.join(BACKEND_DIR, "prompts")


def load_prompt(filename: str) -> dict:
    file_path = os.path.join(PROMPT_DIR, filename)
    with open(file_path, "r") as file:
        return json.load(file)


async def input_handler(state: MessagesState) -> MessagesState:
    # Sentiment analysis
    system_instruction = load_prompt("input_handler_system_instruction.json")[
        "system_instruction"
    ]
    full_prompt = (
        (system_instruction)
        + ("\n\nBased on the following user input:\n\n")
        + (state["messages"][-1].content)
        + ("\n\nExtract the topic.")
    )
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)  # Fast, flexible
    topic = (await llm.ainvoke([full_prompt])).content
    state["topic"] = topic
    return state


def query_router(state: MessagesState) -> str:
    topic = state.get("topic")
    if topic == "unclear":
        return "create_unsure_prompt"
    else:
        mode = state.get("mode")
        if mode == "recap":
            return "create_recap_query"
        elif mode == "forecast":
            return "create_forecast_query"
        else:
            return "create_general_prompt"


async def create_general_prompt(state: MessagesState) -> MessagesState:
    system_instruction = load_prompt("create_general_prompt_system_instruction.json")[
        "system_instruction"
    ]
    topic = state.get("topic")
    full_prompt = (
        (system_instruction)
        + ("\n\nBased on the following topic:\n\n")
        + topic
        + ("\n\nGenerate the prompt.")
    )
    llm = ChatOpenAI(model="o4-mini")
    response = await llm.ainvoke([full_prompt])
    system_message = SystemMessage(content=(response.content))
    state["messages"].append(system_message)
    return state


async def create_recap_query(state: MessagesState) -> MessagesState:
    system_instruction = load_prompt("create_recap_query_system_instruction.json")[
        "system_instruction"
    ]
    full_prompt = (
        (system_instruction)
        + ("\n\nHere is the topic that the user specified:\n\n")
        + state.get("topic")
        + ("\n\nHere is the timeframe that the user specified:\n\n")
        + state.get("timeframe")
        + ("\n\nHere is today's date:\n\n")
        + ((datetime.now().date()).strftime("%B %d, %Y"))
        + ("\n\nNow formulate your query.")
    )
    llm = ChatOpenAI(model="o4-mini")
    response = await llm.ainvoke([full_prompt])
    system_message = SystemMessage(content=(response.content))
    state["messages"].append(system_message)
    return state


async def create_forecast_query(state: MessagesState) -> MessagesState:
    system_instruction = load_prompt("create_forecast_query_system_instruction.json")[
        "system_instruction"
    ]
    full_prompt = (
        (system_instruction)
        + ("\n\nHere is the topic that the user specified:\n\n")
        + state.get("topic")
        + ("\n\nHere is the timeframe that the user specified:\n\n")
        + state.get("timeframe")
        + ("\n\nHere is today's date:\n\n")
        + ((datetime.now().date()).strftime("%B %d, %Y"))
        + ("\n\nNow formulate your query.")
    )
    llm = ChatOpenAI(model="o4-mini")
    response = await llm.ainvoke([full_prompt])
    system_message = SystemMessage(content=(response.content))
    state["messages"].append(system_message)
    return state


async def run_search(state: MessagesState) -> MessagesState:
    # Use SERP tool
    search_query = state["messages"][-1].content.strip('"').strip()
    tavily_search_tool = TavilySearchResults(max_results=4)
    search_results = tavily_search_tool.invoke(search_query)  # list of dicts
    search_results_string = str(search_results)
    system_message = SystemMessage(content=(search_results_string))
    state["messages"].append(system_message)
    return state


def response_router(state: MessagesState) -> str:
    mode = state.get("mode")
    if mode == "recap":
        return "create_recap_prompt"
    elif mode == "forecast":
        return "create_forecast_prompt"


async def create_recap_prompt(state: MessagesState) -> MessagesState:
    system_instruction = load_prompt("create_recap_prompt_system_instruction.json")[
        "system_instruction"
    ]
    full_prompt = (
        (system_instruction)
        + ("\n\nHere is the topic that the user specified:\n\n")
        + state.get("topic")
        + ("\n\nHere is the timeframe that the user specified:\n\n")
        + state.get("timeframe")
        + ("\n\nHere is today's date:\n\n")
        + ((datetime.now().date()).strftime("%B %d, %Y"))
        + ("\n\nHere are the search results from the SERP tool:\n\n")
        + state["messages"][-1].content
        + ("\n\n\nNow construct your prompt.\n\n")
    )
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)  # Fast, flexible
    response = await llm.ainvoke([full_prompt])
    system_message = SystemMessage(content=(response.content))
    state["messages"].append(system_message)
    return state


async def create_forecast_prompt(state: MessagesState) -> MessagesState:
    system_instruction = load_prompt("create_forecast_prompt_system_instruction.json")[
        "system_instruction"
    ]
    full_prompt = (
        (system_instruction)
        + ("\n\nHere is the topic that the user specified:\n\n")
        + state.get("topic")
        + ("\n\nHere is the timeframe that the user specified:\n\n")
        + state.get("timeframe")
        + ("\n\nHere is today's date:\n\n")
        + ((datetime.now().date()).strftime("%B %d, %Y"))
        + ("\n\nHere are the search results from the SERP tool:\n\n")
        + state["messages"][-1].content
        + ("\n\nNow construct your prompt.\n\n")
    )
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)  # Fast, flexible
    response = await llm.ainvoke([full_prompt])
    system_message = SystemMessage(content=(response.content))
    state["messages"].append(system_message)
    return state


async def create_unsure_prompt(state: MessagesState) -> MessagesState:
    system_instruction = load_prompt("create_unsure_prompt_system_instruction.json")[
        "system_instruction"
    ]
    system_message = SystemMessage(content=(system_instruction))
    state["messages"].append(system_message)
    return state


async def generate_final_response(state: MessagesState):
    # Set model temperature based on the user-specified mode
    mode = state.get("mode")
    model = state.get("model", "gpt-4o")
    llm = ChatOpenAI(
        model=model, streaming=True, temperature=0.4 if mode == "forecast" else 0.0
    )

    # Generate final response
    print("Generating final response...")
    prompt = state["messages"][-1].content
    full = ""
    for chunk in await llm.ainvoke([prompt]):
        yield {"messages": [chunk]}
    state["messages"].append(AIMessage(content=full))
    yield state


# Create graph
builder = StateGraph(MessagesState)


# Add nodes
builder.add_node("input_handler", input_handler)
builder.add_node("create_recap_query", create_recap_query)
builder.add_node("create_forecast_query", create_forecast_query)
builder.add_node("run_search", run_search)
builder.add_node("create_recap_prompt", create_recap_prompt)
builder.add_node("create_forecast_prompt", create_forecast_prompt)
builder.add_node("create_general_prompt", create_general_prompt)
builder.add_node("create_unsure_prompt", create_unsure_prompt)
builder.add_node("generate_final_response", generate_final_response)


# Add edges
builder.add_edge(START, "input_handler")
builder.add_conditional_edges("input_handler", query_router)
builder.add_edge("create_recap_query", "run_search")
builder.add_edge("create_forecast_query", "run_search")
builder.add_conditional_edges("run_search", response_router)
builder.add_edge("create_recap_prompt", "generate_final_response")
builder.add_edge("create_forecast_prompt", "generate_final_response")
builder.add_edge("create_general_prompt", "generate_final_response")
builder.add_edge("create_unsure_prompt", "generate_final_response")
builder.add_edge("generate_final_response", END)


# Compile graph
graph = builder.compile()


# API chat endpoint
@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    # Create LangSmith API client
    client = get_client(url=GRAPH_URL, api_key=GRAPH_KEY)
    assistant_id = "recap-and-forecast-bot"
    thread = await client.threads.create()
    """

    async def event_stream():
        # Initialize conversation state based on incoming API request
        input_state = {
            "messages": [HumanMessage(content=request.message)],
            "mode": request.mode,
            "timeframe": request.timeframe,
            "model": request.model,
        }

        # Stream tokens and metadata objects
        async for msg, metadata in graph.astream(
            input_state,
            stream_mode="messages",
        ):

            # Skip outputs from other nodes
            if metadata.get("langgraph_node") != "generate_final_response":
                continue

            # Skip system messages / tool messages
            if msg.type not in ("AIMessage", "AIMessageChunk"):
                continue

            content = getattr(msg, "content", None)
            if content:
                yield content.encode()

    return StreamingResponse(event_stream(), media_type="text/plain")
