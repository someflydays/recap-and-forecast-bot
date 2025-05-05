import os
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
    AIMessageChunk,
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


# Define API response schema, validated with Pydantic
class ChatResponse(BaseModel):
    response: str


# Define graph state schema
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    mode: str
    timeframe: str
    topic: str


async def input_handler(state: MessagesState) -> MessagesState:
    # Sentiment analysis
    system_instruction = "You are a topic extractor. The user has been asked to specify a topic. Your goal is to analyze the user's input and identify the topic that they are trying to specify. Based on the user's input, extract the topic that they most likely are trying to specify. Consider that they might make a typo, so if the input is not grammatically correct, then try to understand what they meant to say. Output the extracted topic as concisely as possible, and do not output anything else. If the user does not seem to be trying to specify any topic, then output one word: unclear"
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
    system_instruction = "You are a prompt engineer. An LLM will be invoked with the prompt that you create. Your job is to create a prompt based on a specified topic. The goal of your prompt is to instruct an LLM to provide a high-level report about the specified topic. Use your best prompt engineering skills to construct your prompt for the LLM. Do not output anything other than the prompt."
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
    system_instruction = "You will be given a topic, a timeframe, and today's date. For example: {'topic': 'AI', 'timeframe': 'this week', 'date' : 'April 21, 2025'}\n\nYour goal is to generate a well-structured query for use in web-search, with the aim of finding the most impactful and most relevant information about what's been happening with the given topic during the given timeframe (relative to today's date)."
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
    system_instruction = "You will be given a topic, a timeframe, and today's date. For example: {'topic': 'AI', 'timeframe': 'this week', 'date' : 'April 21, 2025'}\n\nYour goal is to generate a well-structured query for use in web-search, with the aim of finding the most impactful and most insightful information about what will most likely happen with the given topic during the given timeframe (relative to today's date). Your query should focus on finding upcoming events, news, or important things that are scheduled to happen during the given timeframe. Your query should also find key information that can later be used for trend analysis about what might happen regarding the topic in the given timeframe. Based on this goal, formulate a well-structured web-search query"
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
    system_instruction = (
        "You are a prompt engineer. An LLM will be invoked with the prompt that you create. Your job is to create a prompt based on given SERP results. Do not output anything other than your prompt.\n\n"
        + "A user has specified a topic, a timeframe, and today's date.\nFor example: {'topic': 'AI', 'timeframe': 'this week', 'date': 'April 21, 2025'}.\n\n"
        + "The user's input has been passed to a SERP tool, which searched the web for news/events/stories/breakthroughs/info about important things that have been happening regarding that topic during the specified timeframe (relative to today's date).\nFor example: if the user's input was {'topic': 'AI', 'timeframe': 'this week', 'date': 'April 21, 2025'}, then the SERP tool searched the web for AI news that's happening the week of April 21, 2025.\n\n"
        + "You will be given the SERP tool's search results, and you need to write a prompt that tells the LLM to list the most relevant search results in a well-formatted report. Each listed search result should include a bold title, a concise one-sentence summary, the link to the search result (as a clickable, italicized hyperlink), and a new line between each of those sections. Don't explicitly say 'Title:' or 'Summary:'. There should be no main title of the report, and tell the LLM to not output anything other than the report. Focus on readability and formatting. Avoid truncating anything - generate your own summary or title. Use your best prompt engineering skills to construct your prompt for the LLM."
    )
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
    system_instruction = (
        "You are a prompt engineer. An LLM will be invoked with the prompt that you create. Your job is to create a prompt based on given SERP results. Do not output anything other than your prompt.\n\n"
        + "A user has specified a topic, a timeframe, and today's date.\nFor example: {'topic': 'AI', 'timeframe': 'this week', 'date': 'April 21, 2025'}.\n\n"
        + "The user's input has been passed to a SERP tool, which searched the web for news/events/stories/breakthroughs/info about that topic, with the goal of gathering enough relevant information to formulate credible speculative insights about what will likely happen during the specified timeframe (relative to today's date).\n\n"
        + "For example: if the user's input was {'topic': 'AI', 'timeframe': 'this week', 'date': 'April 21, 2025'}, then the SERP tool searched the web for news/stories/events/articles about AI with the goal of eventually using that information for trend analysis to generate a report about specific things that will happen regarding AI this week (with sources), and credible speculative ideas about what is likely to happen regarding AI this week (with reasoning).\n\n"
        + "You will be given the SERP tool's search results, and you need to write a prompt that tells the LLM to generate this report. Each deterministic upcoming event in the report should include a bold title, a one-sentence summary, a link to the relevant search result (as a clickable, italicized hyperlink), and a new line between each of those sections. Each prediction in the report should include a bold title, a concise summary, a justification section where the user can see exactly why this insight has been predicted, and a new line between each of those sections. There should be no main title of the report, and tell the LLM to not output anything other than the report. Tell the LLM to focus on report readability and formatting. Avoid truncating anything - generate your own summary or title. Add a two new lines to separate each result. Use your best prompt engineering skills to construct your prompt for the LLM."
    )
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
    system_instruction = "Please tell the user that you are unsure what topic they are trying to specify, and suggest that they specify a topic in the text box. Do not output anything other than your message to the user."
    system_message = SystemMessage(content=(system_instruction))
    state["messages"].append(system_message)
    return state


async def generate_final_response(state: MessagesState):
    # Set model temperature based on the user-specified mode
    mode = state.get("mode")
    llm = ChatOpenAI(
        model="gpt-4o", streaming=True, temperature=0.4 if mode == "forecast" else 0.0
    )

    # Generate final response
    print("Generating final response...")
    prompt = state["messages"][-1].content
    # final_response = await llm.ainvoke([prompt])
    # return {"messages": [final_response]}
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
