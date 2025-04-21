# Recap and Forecast Bot

Python version: 3.13.3

## Repository structure:

```
recap-and-forecast-bot/
    backend/
        app/
            chatbot.py
        README.md
        Dockerfile
        requirements.txt
    frontend/
        README.md
    infrastructure/
        docker-compose.yml
    README.md
    .gitignore
```

## Setup

This project utilizes the OpenAI API. Please sign up for an API key and store it as an environment variable. You can do this by navigating to the project's root directory and running the following command:
```
mkdir -p ./backend && echo "OPENAI_API_KEY=your_api_key" > ./backend/.env
```
