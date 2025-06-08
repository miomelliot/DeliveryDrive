FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
ENV TZ=Europe/Moscow \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Копируем только то, что нужно для зависимостей
COPY pyproject.toml .
COPY uv.lock .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# исходники
COPY src ./src
COPY static ./static
RUN mkdir -p ./static/icons

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
