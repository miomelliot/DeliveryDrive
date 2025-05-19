# ---------- base image ----------
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# ---------- env & workdir ----------
WORKDIR /app
ENV TZ=Europe/Moscow \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# ---------- install prod deps ----------
# pyproject.toml и uv.lock находятся в app/orm-server/
COPY app/orm-server/pyproject.toml \
    app/orm-server/uv.lock \
    ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# ---------- copy service code ----------
# 1) сам orm-server
COPY app/orm-server/src ./src
# 2) общие gRPC stubs
COPY app/shared ./shared

# при необходимости докинуть другие общие модули:
# COPY app/shared/utils ./shared/utils

# ---------- install project-internal deps ----------
# если pyproject.toml помечает src как пакет, тянем его сюда:
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---------- entrypoint ----------
CMD ["uv", "run", "src/run_grpc.py"]
