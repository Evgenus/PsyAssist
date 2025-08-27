FROM python:3.12-slim

# Set environment variables to prevent threading issues
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_PROGRESS_BAR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_BUILD_ISOLATION=1
ENV PIP_NO_INDEX=0
ENV PIP_PREFER_BINARY=1
ENV PIP_QUIET=1

# Set working directory
WORKDIR /app

# Install system dependencies for health check
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true

# Copy project files
COPY pyproject.toml .
COPY README.md .
COPY psyassist/ ./psyassist/
COPY run.py .
COPY env.example .

# Install Python dependencies using a different approach
RUN python -m pip install --quiet --no-cache-dir --disable-pip-version-check setuptools wheel
RUN python -m pip install --quiet --no-cache-dir --disable-pip-version-check fastapi uvicorn pydantic pydantic-settings httpx python-dotenv
RUN python -m pip install --quiet --no-cache-dir --disable-pip-version-check openai anthropic cryptography structlog
RUN python -m pip install --quiet --no-cache-dir --disable-pip-version-check crewai

# Copy and install the local package
COPY . .
RUN python -m pip install --quiet --no-cache-dir --disable-pip-version-check -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "run.py"]
