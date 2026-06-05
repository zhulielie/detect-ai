FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY detect_ai/ ./detect_ai/
COPY web/ ./web/
COPY examples/ ./examples/

RUN pip install --no-cache-dir -e ".[web]"

EXPOSE 5001

ENV FLASK_APP=web/app.py

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5001"]
