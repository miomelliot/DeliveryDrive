from pathlib import Path

import nox

nox.options.default_venv_backend = "uv|virtualenv"
nox.options.sessions = ["ruff", "ruff_format", "mypy"]

#  ──┐  api-server/noxfile.py
#    └─ parent*2 →  <repo root>/app
BASE_DIR: Path = Path(__file__).resolve().parent.parent  # <-- app/
PROTO_DIR: Path = BASE_DIR / "shared" / "protos"  # app/shared/protos
OUT_DIR: Path = BASE_DIR / "shared" / "grpc_stubs"  # app/shared/grpc_stubs


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
    session.run("mypy", ".", "--exclude", "tests/|build/", external=True)


@nox.session(reuse_venv=True)
def tests(session: nox.Session) -> None:
    session.install(".[dev]")
    session.run("pytest", "tests/", external=True)


@nox.session(python=False)
def gen_protos(session: nox.Session) -> None:
    """Генерация gRPC stubs из .proto → app/shared/grpc_stubs"""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for proto_file in PROTO_DIR.glob("*.proto"):
        session.run(
            "python",
            "-m",
            "grpc_tools.protoc",
            f"-I{PROTO_DIR}",
            f"--python_out={OUT_DIR}",
            f"--grpc_python_out={OUT_DIR}",
            str(proto_file),
            external=True,
        )
