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

# Set up LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Define API request schema
class ChatRequest(BaseModel):
    message: str
    mode: str # "recap", "foresight", "general"
    timeframe: str # "today", "this week", etc.
    
# Define API response schema
class ChatResponse(BaseModel):
    response: str

# Define graph state schema
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def input_handler(state: MessagesState) -> dict:
    pass
    
def router(state: MessagesState) -> str:
    mode = state.get("mode")
    if mode == "recap":
        return "generate_recap_query"
    elif mode == "foresight":
        return "generate_foresight_query"
    else:
        return "generate_direct_response"
    
def generate_recap_query(state: MessagesState) -> dict:
    pass

def generate_foresight_query(state: MessagesState) -> dict:
    pass
    
def run_search(state: MessagesState) -> dict:
    pass
    
def generate_serped_response(state: MessagesState) -> dict:
    pass
    
def generate_direct_response(state: MessagesState) -> dict:
    pass

builder = StateGraph(MessagesState)
builder.add_node("input_handler", input_handler)
builder.add_node("generate_recap_query", generate_recap_query)
builder.add_node("generate_foresight_query", generate_foresight_query)
builder.add_node("run_search", run_search)
builder.add_node("generate_serped_response", generate_serped_response)
builder.add_node("generate_direct_response", generate_direct_response)

builder.add_edge(START, "input_handler")
builder.add_conditional_edges("input_handler", router)
builder.add_edge("generate_recap_query", "run_search")
builder.add_edge("generate_foresight_query", "run_search")
builder.add_edge("run_search", "generate_serped_response")
builder.add_edge("generate_serped_response", END)
builder.add_edge("generate_direct_response", END)

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
