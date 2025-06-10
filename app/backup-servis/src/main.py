from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from src.utils import run_cmd
from src.core.config import Settings, get_settings

settings: Settings = get_settings()
scheduler = BlockingScheduler(timezone="Europe/Moscow")

def diff_backup() -> None:
    filename: str = f"/backups/diff_{datetime.now():%Y-%m-%d_%H-%M}.dump"
    run_cmd(
        f"pg_dump -Fc -f {filename} "
        f"-h {settings.host} -p {settings.port} "
        f"-U {settings.user} {settings.db}"
    )

def full_backup() -> None:
    dirname: str = f"/backups/full_{datetime.now():%Y-%m-%d_%H-%M}"
    run_cmd(
        f"pg_basebackup -D {dirname} -F tar -z -X fetch "
        f"-h {settings.host} -p {settings.port} -U {settings.user}"
    )

def wal_backup() -> None:
    timestamp: str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    run_cmd(f"cp -r /var/lib/postgresql/data/pg_wal /backups/wal_{timestamp}")

def globals_backup() -> None:
    filename: str = f"/backups/globals_{datetime.now():%Y-%m-%d_%H-%M}.sql"
    run_cmd(
        f"pg_dumpall --globals-only "
        f"-h {settings.host} -p {settings.port} -U {settings.user} > {filename}"
    )

scheduler.add_job(diff_backup, 'cron', day_of_week='mon-fri', hour=21)
scheduler.add_job(full_backup, 'cron', day_of_week='sat', hour=22)
scheduler.add_job(wal_backup, 'cron', day_of_week='mon-fri', hour='10-18')
scheduler.add_job(globals_backup, 'cron', day_of_week='sat', hour=20)

scheduler.start()
