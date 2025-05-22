# FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# WORKDIR /app
# ENV TZ=Europe/Moscow \
#     UV_COMPILE_BYTECODE=1 \
#     UV_LINK_MODE=copy \
#     PYTHONUNBUFFERED=1

# # Копируем только то, что нужно для зависимостей
# COPY app/orm-server/pyproject.toml .
# COPY app/orm-server/uv.lock .

# # Устанавливаем зависимости (с проектом!), без dev-зависимостей
# RUN --mount=type=cache,target=/root/.cache/uv \
#     uv sync --frozen --no-dev
# # ТУТ УБРАЛИ --no-install-project, UV поставил и твой пакет — плагин-grpc отработал

# # Теперь копируем код
# COPY app/orm-server/src ./src
# COPY app/shared ./src/shared

# # (опционально) Проверим, что stubs появились
# RUN ls src/shared/grpc_stubs

# ENV PATH="/app/.venv/bin:$PATH"
# CMD ["uv", "run", "src/run_grpc.py"]
