FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy pyproject.toml first to generate lockfile
COPY pyproject.toml .

# Generate lockfile
RUN uv lock

# Copy the rest of the application code
COPY . .

# Install dependencies
RUN uv sync --frozen --no-dev

EXPOSE 8080

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "uvicorn", "mcp_gsheets:server", "--host", "0.0.0.0", "--port", "8080"]
