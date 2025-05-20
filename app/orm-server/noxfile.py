from pathlib import Path

import nox

nox.options.default_venv_backend = "uv|virtualenv"
nox.options.sessions = ["ruff", "ruff_format", "mypy"]


@nox.session(reuse_venv=True)
def ruff(session: nox.Session) -> None:
    session.install(".[dev]")
    session.run("ruff", "check", ".", external=True)


@nox.session(reuse_venv=True)
def ruff_format(session: nox.Session) -> None:
    session.install(".[dev]")
    session.run("ruff", "format", ".", external=True)
    session.run("ruff", "check", "--select", "I", "--fix", ".", external=True)


@nox.session(reuse_venv=True)
def mypy(session: nox.Session) -> None:
    session.install(".[dev]")
    session.run("mypy", ".", "--exclude", "tests/|build/|shared/", external=True)


@nox.session(reuse_venv=True)
def tests(session: nox.Session) -> None:
    session.install(".[dev]")
    session.run("pytest", "tests/", external=True)


#  ──┐  api-server/noxfile.py
#    └─ parent*2 →  <repo root>/app
# Путь до корня репозитория (DeliveryDrive/)
BASE_DIR: Path = Path(__file__).resolve().parent.parent  # <repo root>
PROTO_DIR: Path = BASE_DIR / "shared" / "protos"  # DeliveryDrive/shared/protos
OUT_DIR: Path = BASE_DIR / "shared"  # DeliveryDrive/shared


@nox.session(python=False)
def gen_protos(session: nox.Session) -> None:
    """Генерация gRPC stubs + .pyi из .proto → shared.grpc_stubs"""
    (OUT_DIR / "grpc_stubs").mkdir(parents=True, exist_ok=True)

    for proto_file in PROTO_DIR.glob("*.proto"):
        session.run(
            "python",
            "-m",
            "grpc_tools.protoc",
            f"-I{PROTO_DIR}",
            f"--python_out={OUT_DIR}",
            f"--grpc_python_out={OUT_DIR}",
            f"--pyi_out={OUT_DIR}",
            str(proto_file),
            external=True,
        )
