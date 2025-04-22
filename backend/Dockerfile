FROM python:3.11-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip wheel \
  && pip install \
    --default-timeout=100 \
    --retries=10 \
    --no-cache-dir \
    -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.chatbot:app", "--host", "0.0.0.0", "--port", "8000"]
