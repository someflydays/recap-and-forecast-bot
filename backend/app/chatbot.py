from fastapi import FastAPI
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

# Load API key
load_dotenv()

# Instantiate FastAPI app
app = FastAPI()

# Set up LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Define request and response schemas
class ChatRequest(BaseModel):
    message: str
class ChatResponse(BaseModel):
    response: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = llm.invoke([HumanMessage(content=request.message)])
    return ChatResponse(response=result.content)
