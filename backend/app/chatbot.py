from fastapi import FastAPI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from pydantic import BaseModel
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.tools.tavily_search import TavilySearchResults
import traceback
from datetime import datetime

# Load API keys
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
creative_streaming_llm = ChatOpenAI(model="gpt-4o", streaming=True, temperature=0.4)

# Define API request schema
class ChatRequest(BaseModel):
    message: str
    mode: str # "recap", "foresight", "general"
    timeframe: str # "today", "this week", etc.
    
# Define API response schema
class ChatResponse(BaseModel):
    response: str

# Define graph state schema
args = TypedDict('MessagesState', {
    "messages": Annotated[list[AnyMessage], add_messages],
    "mode": str,
    "timeframe": str,
    "topic": str
})
class MessagesState(args):
    pass

"""
Define nodes and router functions
"""
def input_handler(state: MessagesState) -> MessagesState:
    system_instruction = (
        "You are a topic extractor. The user has been asked to specify a topic. Your goal is to analyze the user's input and identify the topic that they are trying to specify. Based on the user's input, extract the topic that they most likely are trying to specify. Output the extracted topic as concisely as possible, and do not output anything else. If the user does not seem to be trying to specify any topic, then output one word: unclear"
    )
    full_prompt = (
        (system_instruction) + ("\n\nBased on the following user input:\n\n") + (state["messages"][-1].content) + ("\n\nExtract the topic.")
    )
    topic = internal_llm.invoke([full_prompt]).content
    state["topic"] = topic
    return state
    
def query_router(state: MessagesState) -> str:
    topic = state.get("topic")
    if topic == "unclear":
        return "generate_unsure_response"
    else:
        mode = state.get("mode")
        if mode == "recap":
            return "create_recap_query"
        elif mode == "foresight":
            return "create_foresight_query"
        else:
            return "create_general_prompt"
        
def create_general_prompt(state: MessagesState) -> MessagesState:
    system_instruction = (
        "You are a prompt engineer. An LLM will be invoked with the prompt that you create. Your job is to create a prompt based on a specified topic. The goal of your prompt is to instruct an LLM to provide a high-level report about the specified topic. Use your best prompt engineering skills to construct your prompt for the LLM. Do not output anything other than the prompt."
    )
    topic = state.get("topic")
    full_prompt = (system_instruction) + ("\n\nBased on the following topic:\n\n") + topic + ("\n\nGenerate the prompt.")
    response = internal_llm.invoke([full_prompt])
    ai_message = AIMessage(content=(response.content))
    state["messages"].append(ai_message)
    return state
    
def generate_general_response(state: MessagesState) -> MessagesState:
    engineered_prompt = state["messages"][-1].content
    response = deterministic_streaming_llm.invoke([engineered_prompt])
    ai_message = AIMessage(content=(response.content))
    state["messages"].append(ai_message)
    return state
    
def create_recap_query(state: MessagesState) -> MessagesState:
    system_instruction = (
        "You will be given a topic, a timeframe, and today's date. For example: {'topic': 'AI', 'timeframe': 'this week', 'date' : 'April 21, 2025'}\n\nYour goal is to generate a well-structured query for use in web-search, with the aim of finding relevant information about what's been happening with the given topic during the given timeframe (relative to today's date)."
    )
    full_prompt = (system_instruction) + ("\n\nHere is the topic that the user specified:\n\n") + state.get("topic") + ("\n\nHere is the timeframe that the user specified:\n\n") + state.get("timeframe") + ("\n\nHere is today's date:\n\n") + ((datetime.now().date()).strftime("%B %d, %Y")) + ("\n\nNow formulate your query.")
    response = internal_llm.invoke([full_prompt])
    ai_message = AIMessage(content=(response.content))
    state["messages"].append(ai_message)
    return state

def create_foresight_query(state: MessagesState) -> MessagesState:
    system_instruction = (
        "You will be given a topic, a timeframe, and today's date. For example: {'topic': 'AI', 'timeframe': 'this week', 'date' : 'April 21, 2025'}\n\nYour goal is to generate a well-structured query for use in web-search, with the aim of finding information about what will most likely happen with the given topic during the given timeframe (relative to today's date). Your query should focus on finding upcoming events, news, or important things that are scheduled to happen during the given timeframe. Your query should also find key information that can later be used for trend analysis about what might happen regarding the topic in the given timeframe. Based on this goal, formulate a well-structured web-search query"
    )
    full_prompt = (system_instruction) + ("\n\nHere is the topic that the user specified:\n\n") + state.get("topic") + ("\n\nHere is the timeframe that the user specified:\n\n") + state.get("timeframe") + ("\n\nHere is today's date:\n\n") + ((datetime.now().date()).strftime("%B %d, %Y")) + ("\n\nNow formulate your query.")
    response = internal_llm.invoke([full_prompt])
    ai_message = AIMessage(content=(response.content))
    state["messages"].append(ai_message)
    return state
    
def run_search(state: MessagesState) -> MessagesState:
    # Use SERP tool
    search_query = state["messages"][-1].content.strip('"').strip()
    tavily_search_tool = TavilySearchResults(max_results=4)
    search_results = tavily_search_tool.invoke(search_query) # list of dicts
    search_results_string = str(search_results)
    ai_message = AIMessage(content=(search_results_string))
    state["messages"].append(ai_message)
    return state
    
def response_router(state: MessagesState) -> str:
    mode = state.get("mode")
    if mode == "recap":
        return "create_recap_prompt"
    elif mode == "foresight":
        return "create_foresight_prompt"
        
def create_recap_prompt(state: MessagesState) -> MessagesState:
    system_instruction = (
        "You are a prompt engineer. An LLM will be invoked with the prompt that you create. Your job is to create a prompt based on given SERP results. Do not output anything other than your prompt.\n\n" + "A user has specified a topic, a timeframe, and today's date.\nFor example: {'topic': 'AI', 'timeframe': 'this week', 'date': 'April 21, 2025'}.\n\n" + "The user's input has been passed to a SERP tool, which searched the web for news/events/stories/breakthroughs/info about important things that have been happening regarding that topic during the specified timeframe (relative to today's date).\nFor example: if the user's input was {'topic': 'AI', 'timeframe': 'this week', 'date': 'April 21, 2025'}, then the SERP tool searched the web for AI news that's happening the week of April 21, 2025.\n\n" + "You will be given the SERP tool's search results, and you need to write a prompt that tells the LLM to list the most relevant search results in a well-formatted report. Each listed search result should include a title, a concise one-sentence summary, and the link to the search result. There should be no main title of the report, and tell the LLM to not output anything other than the report. Please ask the LLM to add an extra newline in between each sub-section of the report. Use your best prompt engineering skills to construct your prompt for the LLM."
    )
    full_prompt = (system_instruction) + ("\n\nHere is the topic that the user specified:\n\n") + state.get("topic") + ("\n\nHere is the timeframe that the user specified:\n\n") + state.get("timeframe") + ("\n\nHere is today's date:\n\n") + ((datetime.now().date()).strftime("%B %d, %Y")) + ("\n\nHere are the search results from the SERP tool:\n\n") + state["messages"][-1].content + ("\n\n\nGenerate your prompt.\n\n")
    response = internal_llm.invoke([full_prompt])
    ai_message = AIMessage(content=(response.content))
    state["messages"].append(ai_message)
    return state
    
def create_foresight_prompt(state: MessagesState) -> MessagesState:
    system_instruction = (
        "You are a prompt engineer. An LLM will be invoked with the prompt that you create. Your job is to create a prompt based on given SERP results. Do not output anything other than your prompt.\n\n" + "A user has specified a topic, a timeframe, and today's date.\nFor example: {'topic': 'AI', 'timeframe': 'this week', 'date': 'April 21, 2025'}.\n\n" + "The user's input has been passed to a SERP tool, which searched the web for news/events/stories/breakthroughs/info about that topic, with the goal of gathering enough relevant information to formulate credible speculative insights about what will likely happen during the specified timeframe (relative to today's date).\n\n" + "For example: if the user's input was {'topic': 'AI', 'timeframe': 'this week', 'date': 'April 21, 2025'}, then the SERP tool searched the web for news/stories/events/articles about AI with the goal of eventually using that information for trend analysis to generate a report about specific things that will happen regarding AI this week (with sources), and credible speculative ideas about what is likely to happen regarding AI this week (with reasoning).\n\n" + "You will be given the SERP tool's search results, and you need to write a prompt that tells the LLM to generate this report. Each deterministic upcoming event in the report should include a title, a one-sentence summary, and a link to the relevant search result. Each prediction in the report should include a title, a concise summary, and a justification section where the user can see exactly why this insight has been predicted. Please ask the LLM to add an extra newline in between each sub-section of the report. There should be no main title of the report, and tell the LLM to not output anything other than the report. Use your best prompt engineering skills to construct your prompt for the LLM."
    )
    full_prompt = (system_instruction) + ("\n\nHere is the topic that the user specified:\n\n") + state.get("topic") + ("\n\nHere is the timeframe that the user specified:\n\n") + state.get("timeframe") + ("\n\nHere is today's date:\n\n") + ((datetime.now().date()).strftime("%B %d, %Y")) + ("\n\nHere are the search results from the SERP tool:\n\n") + state["messages"][-1].content + ("\n\nGenerate your prompt.\n\n")
    response = internal_llm.invoke([full_prompt])
    ai_message = AIMessage(content=(response.content))
    state["messages"].append(ai_message)
    return state
    
def generate_unsure_response(state: MessagesState) -> MessagesState:
    system_instruction = (
        "Please tell the user that you are unsure what topic they are trying to specify, and suggest that they specify a topic in the text box. Do not output anything other than your message to the user."
    )
    response = creative_streaming_llm.invoke([system_instruction])
    ai_message = AIMessage(content=(response.content))
    state["messages"].append(ai_message)
    return state
    
def generate_deterministic_serped_response(state: MessagesState) -> MessagesState:
    engineered_prompt = state["messages"][-1].content
    response = deterministic_streaming_llm.invoke([engineered_prompt])
    ai_message = AIMessage(content=(response.content))
    state["messages"].append(ai_message)
    return state
    
def generate_creative_serped_response(state: MessagesState) -> MessagesState:
    engineered_prompt = state["messages"][-1].content
    response = creative_streaming_llm.invoke([engineered_prompt])
    ai_message = AIMessage(content=(response.content))
    state["messages"].append(ai_message)
    return state

# Create graph
builder = StateGraph(MessagesState)

# Add nodes
builder.add_node("input_handler", input_handler)
builder.add_node("create_recap_query", create_recap_query)
builder.add_node("create_foresight_query", create_foresight_query)
builder.add_node("create_general_prompt", create_general_prompt)
builder.add_node("generate_general_response", generate_general_response)
builder.add_node("generate_unsure_response", generate_unsure_response)
builder.add_node("run_search", run_search)
builder.add_node("create_recap_prompt", create_recap_prompt)
builder.add_node("create_foresight_prompt", create_foresight_prompt)
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
builder.add_edge("generate_unsure_response", END)
builder.add_conditional_edges("run_search", response_router)
builder.add_edge("create_recap_prompt", "generate_deterministic_serped_response")
builder.add_edge("create_foresight_prompt", "generate_creative_serped_response")
builder.add_edge("generate_deterministic_serped_response", END)
builder.add_edge("generate_creative_serped_response", END)

# Compile graph
graph = builder.compile()

# API chat endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # Initialize conversation state based on incoming API request
    state = {
        "messages": [HumanMessage(content=request.message)],
        "mode": request.mode,
        "timeframe": request.timeframe,
    }
    try:
        # Invoke the graph
        result = graph.invoke(state)
    except Exception as e:
        print("ERROR INVOKING GRAPH:")
        traceback.print_exc()
        return ChatResponse(response="Hmm, something went wrong. Try again in a moment.")
        
    # print(result["messages"][-1].content)
        
    # Return the last message in the state (the AI response)
    return ChatResponse(response=result["messages"][-1].content)
