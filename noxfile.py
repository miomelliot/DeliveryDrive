import nox


@nox.session
def build_orm(session: nox.Session) -> None:
    """Собирает Docker-образ orm-server из корня проекта."""
    session.run(
        "docker",
        "build",
        "-f",
        "app/orm-server/Dockerfile",
        "-t",
        "deliverydrive:orm-latest",
        ".",
        external=True,
    )
