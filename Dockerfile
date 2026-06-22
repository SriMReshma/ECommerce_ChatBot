FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    CHAINLIT_APP_ROOT=/tmp/ecombot-chainlit

WORKDIR /app

RUN mkdir -p /tmp/ecombot-chainlit

COPY requirements.txt requirements-optional.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY . .

RUN python -m src.rag.embed_catalog

EXPOSE 8000

CMD ["python", "-m", "chainlit", "run", "src/ui/app.py", "--host", "0.0.0.0", "--port", "8000", "--headless"]
