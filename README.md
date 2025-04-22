# Recap and Forecast Bot

## Repository Structure

```
recap-and-forecast-bot/
    backend/
        app/
            chatbot.py
        Dockerfile
        requirements.txt
	.pre-commit-config.yaml
    frontend/
        app/
            globals.css
            layout.tsx
            page.tsx
        components/
            ChatForm.tsx
        Dockerfile
        tailwind.config.js
        postcss.config.js
        package.json
        package-lock.json
        next-env.d.ts
        tsconfig.json
    infrastructure/
        docker-compose.yml
    .gitignore
    README.md
```
<br>

## Setup

This project utilizes the OpenAI API and the Tavily API. Please visit their websites to sign up for API keys, and store them as an environment variables. You can do this by running the following commands from the project's root directory:
```
mkdir -p ./backend && echo "OPENAI_API_KEY=your_api_key" > ./backend/.env
```
```
echo "TAVILY_API_KEY=your_api_key" > ./backend/.env
```
<br>

## Running the App

### Option 1: Using Docker

> **Note:** Make sure you have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

From the project's root directory, run the following command:
```
docker compose --file infrastructure/docker-compose.yml up --build
```

### Option 2: Local Development

If you would like to spin up the backend and frontend for development, run the following commands sequentially:

1. Create and activate a venv (optional, but recommended):
```
python -m venv venv
```
```
source venv/bin/activate
```

2. Install dependencies by running this command from the `recap-and-forecast-bot/` directory:
```
pip install -r backend/requirements.txt
```

3. Start the backend by running this command from the `recap-and-forecast-bot/backend/` directory
```
uvicorn app.chatbot:app --reload
```
Then navigate to http://localhost:8000 in a browser to access the backend.

4. Start the frontend by running this command from the `recap-and-forecast-bot/frontend/` directory:
```
npm run dev
```
Then navigate to http://localhost:3000 in a browser to access the frontend.

5. (OPTIONAL) Enable a Git hook for pre-commit linting by running this command from the `recap-and-forecast-bot/backend/` directory:
```
pre-commit install
```
<br>

## Authentication and Deployment Considerations

### Deployment
- Prepare Docker images for production (multi-stage builds, light-weight structure)
- Push images to a registry (Docker Hub)
- Deploy on a secure cloud (AWS, GCP, Azure)
- Configure a public domain and dynamic load balancer

### Authentication
- API keys and other environment variables stored securely in cloud provider's secret manager
- Rotate keys periodically and revoke compromised keys
- OPTIONAL: OAuth2 for 3rd-party integrations (such as Google Calendar, etc.) with renewal ticket encrypted at rest

<br>

## Prioritizations

Given this project's need for speed and focus on backend development, I prioritized the following tasks according to urgency and data-dependencies:
1. Complete most lessons in the Intro to LangGraph course, focusing on the most relevant lessons to this project
2. Decide on scoped use case for this project
3. Set up basic monorepo structure with blank files
4. Maintain a quick, offline log of design decisions and prioritizations
5. Build basic backend (LangChain, simple FastAPI endpoint, and test with curl)
6. Containerize backend (minimal Dockerfile and docker-compose setup)
7. Document basic build instructions (API keys, .env file, commands, etc)
8. Create scaffolding of backend graph
9. Build simple frontend (simple one-page Next.js app with Tailwind and shadcn UI components)
10. Ensure the frontend can call the backend and display a written response
11. Define clear API schema
12. Containerize frontend and add to docker-compose
13. Implement the majority of backend graph logic
14. Refine backend graph logic and UI together, iteratively
15. Refine system-level prompting
16. Reduce time-to-first-token by streaming LLM outputs to the UI
17. Improve real-time status updates and loading indicators
18. Refine README documentation here and there
19. Add pre-commit hook for Black to help lint my Python code
------------ (below are tasks that are yet to be implemented)
20. Create langgraph.json and use langgraph-sdk to asynchronously stream tokens and status updates to the UI
21. Set up LangGraph Studio or LangSmith
22. Add RAG capabilities, parallelization, conversation history, 3rd-party integrations
23. Prepare Docker images for deployment

## Design Decisions
- I havn't yet set up the langgraph-sdk to stream tokens directly from my graph, so I decided that my graph would return a final prompt which then gets invoked and streamed to the UI from outside of the graph.
- I decided to instantiate a new model within each node, for more control over applying the right models to the right tasks.
- For internal communication between LLMs and for deterministic reporting of web-search results, I opted for a fast model with low temperature settings (OpenAI's 4o-mini).
- For speculative reporting on web-search results, I raised the model's temperature settings.
- For search query generation, I opted for an affordable reasoning model (OpenAI's o4-mini).
- I included a Cancel Response button, status updates, and error codes to improve user engagement and adhere to Nielsen's Usability Heuristics for Interface Design.
- I decided to cross-build the frontend's Docker image for linux/amd64 for more compatibility with various cloud providers.

## AI Tooling Used
Given that this project was mainly backend-focused, I decided to prioritize refining the backend myself while using AI tooling for much of the UI implementation. However, I still made all design decisions and I connected the frontend to the backend.

I used ChatGPT for:
- Implementing UI
- Brainstorming use cases (although I thought of this use case!)
- Reviewing LangGraph course material and asking questions
- Formulating .gitignore and .dockerignore
- Help with imported libraries and dependencies
- Polishing documentation

I used Cursor IDE for:
- Development and debugging