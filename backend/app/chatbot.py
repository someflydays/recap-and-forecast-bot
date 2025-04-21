from fastapi import FastAPI
from langchain_core.messages import HumanMessage, AnyMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from pydantic import BaseModel
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from fastapi.middleware.cors import CORSMiddleware

# Load API key
load_dotenv()

# Instantiate FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up LLMs
internal_llm = ChatOpenAI(model="gpt-4o", temperature=0)
deterministic_streaming_llm = ChatOpenAI(model="gpt-4o", streaming=True, temperature=0)
creative_streaming_llm = ChatOpenAI(model="gpt-4o", streaming=True, temperature=0.6)

# Define API request schema
class ChatRequest(BaseModel):
    message: str
    mode: str # "recap", "foresight", "general"
    timeframe: str # "today", "this week", etc.
    
# Define API response schema
class ChatResponse(BaseModel):
    response: str

# Define graph state schema
args = TypeDict('MessagesState', {
    messages: Annotated[list[AnyMessage], add_messages],
    mode: str,
    timeframe: str,
    token: str
})
class MessagesState(args):
    pass

"""
Define nodes and router functions
"""
def input_handler(state: MessagesState) -> MessagesState:
    # TODO: Add logic to process user input
    return state # For now, return state
    
def query_router(state: MessagesState) -> str:
    mode = state.get("mode")
    if mode == "recap":
        return "create_recap_query"
    elif mode == "foresight":
        return "create_foresight_query"
    else:
        return "create_general_prompt"
    
def create_recap_query(state: MessagesState) -> MessagesState:
    # TODO: Call internal_llm
    pass

def create_foresight_query(state: MessagesState) -> MessagesState:
    # TODO: Call internal_llm
    pass
    
def create_general_prompt(state: MessagesState) -> MessagesState:
    # TODO: Call internal_llm
    pass
    
def run_search(state: MessagesState) -> MessagesState:
    # TODO: Use SERP tool
    pass
    
def response_router(state: MessagesState) -> str:
    mode = state.get("mode")
    if mode == "recap":
        return "generate_deterministic_serped_response"
    elif mode == "foresight":
        return "generate_creative_serped_response"
    else:
        return "generate_general_response"
    
def generate_deterministic_serped_response(state: MessagesState) -> MessagesState:
    # TODO: Call deterministic_streaming_llm
    pass
    
def generate_creative_serped_response(state: MessagesState) -> MessagesState:
    # TODO: Call creative_streaming_llm
    pass
    
def generate_general_response(state: MessagesState) -> MessagesState:
    # TODO: Call deterministic_streaming_llm
    pass

# Create graph
builder = StateGraph(MessagesState)

# Add nodes
builder.add_node("input_handler", input_handler)
builder.add_node("create_recap_query", create_recap_query)
builder.add_node("create_foresight_query", create_foresight_query)
builder.add_node("create_general_prompt", create_general_prompt)
builder.add_node("run_search", run_search)
builder.add_node("generate_general_response", generate_general_response)
builder.add_node(
    "generate_deterministic_serped_response",
    generate_deterministic_serped_response
)
builder.add_node(
    "generate_creative_serped_response",
    generate_creative_serped_response
)

# Add edges
builder.add_edge(START, "input_handler")
builder.add_conditional_edges("input_handler", query_router)
builder.add_edge("create_recap_query", "run_search")
builder.add_edge("create_foresight_query", "run_search")
builder.add_edge("create_general_prompt", "generate_general_response")
builder.add_edge("generate_general_response", END)
builder.add_conditional_edges("run_search", response_router)
builder.add_edge("generate_deterministic_serped_response", END)
builder.add_edge("generate_creative_serped_response", END)

# Compile graph
graph = builder.compile()

# API chat endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    state = {
        "messages": [HumanMessage(content=request.message)],
        "mode": request.mode,
        "timeframe": request.timeframe,
    }
    result = graph.invoke(state)
    return ChatResponse(response=result["messages"][-1].content)
