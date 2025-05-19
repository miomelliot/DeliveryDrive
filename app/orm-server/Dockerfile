FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

ENV TZ=Europe/Moscow \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Копируем зависимости
COPY app/orm-server/pyproject.toml .
COPY app/orm-server/uv.lock .

# Ставим зависимости без dev
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Копируем исходники orm-server
COPY app/orm-server/src ./src

# Копируем shared код (в т.ч. gRPC stubs)
COPY app/shared ./src/shared

# Повторная проверка зависимостей
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Добавляем .venv/bin в PATH
ENV PATH="/app/.venv/bin:$PATH"

CMD ["uv", "run", "src/run_grpc.py"]
