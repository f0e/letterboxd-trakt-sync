from . import console
from .config import load_config
from .sync import sync_letterboxd_diary
from .trakt import trakt_init


def run():
    config = load_config()
    if not config:
        return

    if len(config.accounts) == 0:
        console.print("No accounts found in config.yml", style="dark_red")
        return

    for account in config.accounts:
        trakt_init(config, account)
        sync_letterboxd_diary(config, account)


if __name__ == "__main__":
    run()
