from __future__ import annotations

from pathlib import Path

import nox

# ────────────────────── Settings ──────────────────────
# Предпочитаем uv‑виртуалки (fallback → virtualenv)
nox.options.default_venv_backend = "uv|virtualenv"
# По умолчанию запускаем генерацию gRPC‑стабов
nox.options.sessions = ["gen_protos"]

# ────────────────────── Paths ─────────────────────────
#   repo_root/
#   ├── app/
#   │   └── shared/{protos, grpc_stubs}
#   └── noxfile.py  ← (вот тут мы и находимся)
ROOT_DIR: Path = Path(__file__).resolve().parent          # repo_root/
APP_DIR: Path = ROOT_DIR / "app"                         # repo_root/app
PROTO_DIR: Path = APP_DIR / "shared" / "protos"        # app/shared/protos
OUT_DIR: Path = APP_DIR / "shared" / "grpc_stubs"      # app/shared/grpc_stubs

# ────────────────────── Sessions ──────────────────────

@nox.session(reuse_venv=True)
def gen_protos(session: nox.Session) -> None:
    """Генерируем Python gRPC stubs (+ .pyi) из *.proto → app/shared/grpc_stubs"""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Ищем .proto в указанной директории (без поддиректорий)
    proto_files: list[str] = [str(p) for p in PROTO_DIR.glob("*.proto")]
    if not proto_files:
        session.error(f"Нет .proto файлов в {PROTO_DIR}")

    # grpcio-tools нужен только для генерации
    session.install("grpcio-tools>=1.63.0", "protobuf>=4.23.0")

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

    # 2. PostgreSQL (Deployment) – ждём готовности прямо через Helm
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
        "--wait",
        "--timeout",
        "5m0s",
        external=True,
    )

    # 3. Котролируем rollout деплоймента, а не statefulset
    _kubectl("rollout", "status", "deployment/pg-k8s")

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