import os
import time
from datetime import datetime

from cronsim import CronSim

from . import console
from .config import load_config
from .sync import sync_letterboxd_diary
from .trakt import trakt_init


def run():
    config = load_config()
    if not config:
        console.print("Config failed to load", style="dark_red")
        return

    if len(config.accounts) == 0:
        console.print("No accounts found in config.yml", style="dark_red")
        return

    for account in config.accounts:
        trakt_init(config, account)
        sync_letterboxd_diary(config, account)

    console.print(
        f"Sync completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        style="green",
    )


def get_next_run_time(cron_schedule):
    now = datetime.now()
    cron_iterator = CronSim(cron_schedule, now)
    return next(cron_iterator)


def scheduler():
    cron_schedule = os.getenv("CRON_SCHEDULE", "0 * * * *")  # Default to hourly

    while True:
        next_run = get_next_run_time(cron_schedule)
        console.print(f"Next scheduled run: {next_run}", style="cyan")

        # sleep until next run time
        sleep_duration = max((next_run - datetime.now()).total_seconds(), 1)
        time.sleep(sleep_duration)

        run()


def main():
    scheduled = os.getenv("SCHEDULED", "false").lower() == "true"

    if scheduled:
        run_on_start = os.getenv("RUN_ON_START", "false").lower() == "true"

        if run_on_start:
            run()

        scheduler()
    else:
        run()


if __name__ == "__main__":
    main()
