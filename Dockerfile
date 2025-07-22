FROM fedora:latest

RUN dnf update -y && \
    dnf install -y python3 python3-pip python3-devel gcc curl && \
    dnf clean all

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY uv.lock .
COPY .env.example .env

# Install dependencies with uv
RUN uv sync --frozen

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY mcp/ ./mcp/
COPY models.yml .
COPY logs/ ./logs/

WORKDIR /app

EXPOSE 8000

ENV PYTHONPATH=/app/backend
ENV DEBUG=false
ENV HOST=0.0.0.0
ENV PORT=8000

CMD ["uv", "run", "python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]