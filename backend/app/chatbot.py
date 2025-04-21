from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load API key
load_dotenv()

# Set up the LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Quick test
if __name__ == "__main__":
    test_message = [HumanMessage(content=f"Testing, 1 2 3!", name="Derek")]
    response = llm.invoke(test_message)
    print(response.content)
