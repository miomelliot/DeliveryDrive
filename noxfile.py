from __future__ import annotations

from pathlib import Path

import nox

# Используем uv как движок venv (fallback на virtualenv, если uv не завезли)
nox.options.default_venv_backend = "uv|virtualenv"
# Запускаем по умолчанию линтеры/тайпчекер
nox.options.sessions = ["ruff", "ruff_format", "mypy"]

#  ──┐  api-server/noxfile.py
#    └─ parent*2 →  <repo root>/app
BASE_DIR: Path = Path(__file__).resolve().parent.parent  # <repo root>/app
PROTO_DIR: Path = BASE_DIR / "shared" / "protos"  # app/shared/protos
OUT_DIR: Path = BASE_DIR / "shared" / "grpc_stubs"  # app/shared/grpc_stubs


@nox.session(reuse_venv=True)
def gen_protos(session: nox.Session) -> None:
    """Генерируем Python gRPC stubs (+ .pyi) из *.proto → app/shared/grpc_stubs"""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    proto_files: list[str] = [str(p) for p in PROTO_DIR.glob("*.proto")]
    if not proto_files:
        session.error(f"Нет .proto файлов в {PROTO_DIR}")

    session.run(
        "python",
        "-m",
        "grpc_tools.protoc",
        f"-I{PROTO_DIR}",
        f"--python_out={OUT_DIR}",
        f"--grpc_python_out={OUT_DIR}",
        f"--pyi_out={OUT_DIR}",
        *proto_files,
        external=True,
    )

    # Делаем папку пакетной, иначе импортов не будет
    (OUT_DIR / "__init__.py").touch(exist_ok=True)


@nox.session(python=False)
def deploy(session: nox.Session) -> None:
    """Деплой dev-инфры в k8s через Helm + kubectl.

    Можно передать namespace позиционным аргументом:
        nox -s deploy -- dev
    """

    namespace: str = session.posargs[0] if session.posargs else "default"

    def _kubectl(*args: str) -> None:
        session.run("kubectl", *args, "-n", namespace, external=True)

    session.log(f"Деплоим в namespace: {namespace!r}")

    # 1. PVC
    _kubectl("apply", "-f", "k8s/pvc.yaml")

    # 2. PostgreSQL (StatefulSet)
    session.run(
        "helm",
        "upgrade",
        "--install",
        "pg",
        "./k8s",
        "-f",
        "k8s/values-pg.yaml",
        "--namespace",
        namespace,
        "--create-namespace",
        external=True,
    )

    # 3. Ждём готовности PG
    _kubectl("rollout", "status", "statefulset/pg-k8s")

    # 4. ORM / приложение
    session.run(
        "helm",
        "upgrade",
        "--install",
        "orm",
        "./k8s",
        "-f",
        "k8s/values-orm.yaml",
        "--namespace",
        namespace,
        external=True,
    )
