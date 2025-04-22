# Recap and Forecast Bot

Python version: 3.13.3

## Repository structure:

```
recap-and-forecast-bot/
    backend/
        app/
            chatbot.py
        Dockerfile
        requirements.txt
        README.md
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
        README.md
    infrastructure/
        docker-compose.yml
    .gitignore
    README.md
```

## Setup

This project utilizes the OpenAI API and the Tavily API. Please visit their websites to sign up for API keys, and store them as an environment variables. You can do this by running the following commands from the project's root directory:
```
mkdir -p ./backend && echo "OPENAI_API_KEY=your_api_key" > ./backend/.env
```
```
echo "TAVILY_API_KEY=your_api_key" > ./backend/.env
```

## Running the app

> **Note:** Make sure you have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

From the project's root directory, run the following command:
```
docker compose --file infrastructure/docker-compose.yml up --build
```
