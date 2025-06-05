import nox

nox.options.default_venv_backend = "uv|virtualenv"
nox.options.sessions = ["ruff", "ruff_format", "mypy"]


@nox.session(
    reuse_venv=True,
)
def ruff(session: nox.Session) -> None:
    session.install(".[dev]")
    session.run("ruff", "check", ".", external=True)


@nox.session(
    reuse_venv=True,
)
def ruff_format(session: nox.Session) -> None:
    session.install(".[dev]")
    session.run("ruff", "format", ".", external=True)
    session.run("ruff", "check", "--select", "I", "--fix", ".", external=True)


@nox.session(reuse_venv=True)
def mypy(session: nox.Session) -> None:
    session.install(".[dev]")
    session.run("mypy", "src", "--exclude=tests/", "--explicit-package-bases", external=True)


@nox.session(reuse_venv=True)
def tests(session: nox.Session) -> None:
    session.install(".[dev]")
    session.run("pytest", "tests/", external=True)


@nox.session(reuse_venv=True)
def serve(session: nox.Session) -> None:
    session.install(".")
    session.run("uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "9090", external=True)
