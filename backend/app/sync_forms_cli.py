"""Run once from cron or Windows Task Scheduler."""
from app.database import SessionLocal
from app.services.form_sync_runner import sync_all_forms


def main():
    with SessionLocal() as db:
        result = sync_all_forms(db)
        print(result)
        if result["failed"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
