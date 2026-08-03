import time
from datetime import datetime

from app.config import load_config
from app.scheduler import get_next_run

from app.processor.processor import process_images


def main():

    config = load_config()

    if config is None:
        raise SystemExit(1)

    print(
        "Image processor scheduler started",
        flush=True
    )

    scheduler = config["scheduler"]

    if not scheduler.get("enabled", False):
        print(
            "Scheduler disabled; running once",
            flush=True
        )
        process_images(config)
        return

    while True:
        next_run = get_next_run(
            scheduler["cron"]
        )

        print(
            f"Next run: {next_run}",
            flush=True
        )

        now = datetime.now(
            next_run.tzinfo
        )

        wait_seconds = (
            next_run - now
        ).total_seconds()

        if wait_seconds > 0:
            time.sleep(wait_seconds)

        process_images(config)


if __name__ == "__main__":
    main()