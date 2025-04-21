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

This project utilizes the OpenAI API. Please sign up for an API key and store it as an environment variable. You can do this by running the following command from the project's root directory:
```
mkdir -p ./backend && echo "OPENAI_API_KEY=your_api_key" > ./backend/.env
```

## Running the app

> **Note:** Make sure you have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
From the project's root directory, run the following command:
```
docker compose --file infrastructure/docker-compose.yml up --build
```
