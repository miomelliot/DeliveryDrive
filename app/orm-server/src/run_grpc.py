# app/orm-server/src/run_grpc.py
from __future__ import annotations

import asyncio
import logging
import os
import signal
from typing import Final

import grpc
from grpc.aio import Server

from db.core import init_database
from services.user_service import UserService
from shared.grpc_stubs import user_pb2_grpc

LOGGER: Final[logging.Logger] = logging.getLogger("grpc")
logging.basicConfig(level=logging.INFO)

GRPC_PORT: Final[int] = int(os.getenv("GRPC_PORT", 50051))


async def start_grpc_server() -> Server:
    """Поднимаем gRPC-сервер (async) и сразу возвращаем его объект."""
    server = grpc.aio.server(
        options=[
            ("grpc.max_send_message_length", 8 * 1024 * 1024),
            ("grpc.max_receive_message_length", 8 * 1024 * 1024),
        ],
    )
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    await server.start()
    LOGGER.info("gRPC server started on :%s", GRPC_PORT)
    return server


async def main() -> None:
    # 1. гарантируем, что БД существует и таблицы созданы
    await init_database()

    # 2. запускаем gRPC-сервер
    server: Server = await start_grpc_server()

    # 3. ловим SIGTERM/SIGINT и ждём graceful shutdown
    stop_event = asyncio.Event()

    def _handle_signal(sig_name: str) -> None:
        LOGGER.info("Got %s, shutting down…", sig_name)
        stop_event.set()

    loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, lambda: _handle_signal("SIGTERM"))
    loop.add_signal_handler(signal.SIGINT, lambda: _handle_signal("SIGINT"))

    # 4. ждём сигнала
    await stop_event.wait()

    await server.stop(grace=5)
    LOGGER.info("gRPC server stopped")


if __name__ == "__main__":
    asyncio.run(main())
