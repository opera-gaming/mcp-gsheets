FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* README.md ./
COPY src/ ./src/
COPY templates/ ./templates/
COPY static/ ./static/
COPY alembic/ ./alembic/
COPY alembic.ini ./

RUN uv pip install --system -e .

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "-m", "mcp_gsheets.http_server"]
