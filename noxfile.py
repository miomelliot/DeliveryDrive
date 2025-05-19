from pathlib import Path
import nox

IMAGE_NAME = "miomelliot/orm-server"
TAG = "latest"

nox.options.default_venv_backend = "uv|virtualenv"
nox.options.sessions = ["deploy_pvc", "deploy_pg", "deploy_orm"]


@nox.session
def build_orm(session: nox.Session) -> None:
    """Собирает Docker-образ orm-server из корня проекта."""
    session.run(
        "docker",
        "build",
        "-f",
        "app/orm-server/Dockerfile",
        "-t",
        f"{IMAGE_NAME}:{TAG}",
        ".",
        external=True,
    )


@nox.session
def push_orm(session: nox.Session) -> None:
    """Публикует Docker-образ orm-server на Docker Hub."""
    session.run("docker", "push", f"{IMAGE_NAME}:{TAG}", external=True)


@nox.session
def kind_up(session) -> None:
    """Создаёт kind кластер с именем deliverydrive."""
    session.run(
        "kind",
        "create",
        "cluster",
        "--name",
        "deliverydrive",
        external=True,
    )


@nox.session
def deploy_pvc(session) -> None:
    session.run(
        "kubectl",
        "create",
        "namespace",
        "deliverydrive",
        external=True,
        success_codes=[0, 1],
    )
    session.run(
        "kubectl",
        "apply",
        "-f",
        "k8s/pvc.yaml",
        "-n",
        "deliverydrive",
        external=True,
    )


@nox.session
def deploy_pg(session) -> None:
    session.run(
        "helm",
        "upgrade",
        "--install",
        "pg",
        "./k8s",
        "-f",
        "k8s/values-pg.yaml",
        "--namespace",
        "deliverydrive",
        "--create-namespace",
        external=True,
    )


@nox.session
def deploy_orm(session) -> None:
    session.run(
        "helm",
        "upgrade",
        "--install",
        "orm",
        "./k8s",
        "-f",
        "k8s/values-orm.yaml",
        "--namespace",
        "deliverydrive",
        external=True,
    )


@nox.session(python=False)
def gen_protos(session: nox.Session) -> None:
    """Генерация gRPC-стабов из .proto и фиксация импортов с помощью protol"""
    proto_src = Path("app/shared/protos")
    out_dir = Path("app/shared/grpc_stubs")
    out_dir.mkdir(parents=True, exist_ok=True)

    proto_files = list(proto_src.glob("*.proto"))
    if not proto_files:
        session.error("Нет .proto файлов в app/shared/protos")

    # Генерация Python-файлов из .proto
    session.run(
        "python", "-m", "grpc_tools.protoc",
        f"-I{proto_src}",
        f"--python_out={out_dir}",
        f"--grpc_python_out={out_dir}",
        *[str(p) for p in proto_files],
        external=True,
    )

    # Фиксация импортов с помощью protol
    session.run(
        "protol",
        "--in-place",
        "--create-package",
        "--python-out", str(out_dir),
        "protoc",
        f"--proto-path={proto_src}",
        *[str(p) for p in proto_files],
        external=True,
    )

    # Убедиться, что директория является Python-пакетом
    init_file = out_dir / "__init__.py"
    if not init_file.exists():
        init_file.touch()