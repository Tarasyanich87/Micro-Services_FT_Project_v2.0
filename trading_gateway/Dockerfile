# Dockerfile for trading_gateway

FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy project files
COPY . .

# Set up virtual environment and install dependencies
RUN /root/.cargo/bin/uv venv && \
    . .venv/bin/activate && \
    /root/.cargo/bin/uv pip install -r requirements.txt && \
    /root/.cargo/bin/uv pip install -e .

# Expose port and run application
EXPOSE 8001
CMD [".venv/bin/uvicorn", "trading_gateway.main:app", "--host", "0.0.0.0", "--port", "8001"]
