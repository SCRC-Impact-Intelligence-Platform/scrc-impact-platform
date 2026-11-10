"""Run Google Forms response synchronization once (cron / Task Scheduler)."""

import argparse

import app.models  # noqa: F401 - register all FK targets with Base.metadata
from app.database import SessionLocal
from app.services.form_sync_runner import sync_all_forms


def main():
    with SessionLocal() as db:
        result = sync_all_forms(db)
        print(result)
        if result["failed"]:
            raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Synchronize responses for SENT Google Form batches once."
    )
    parser.parse_args()
    main()
