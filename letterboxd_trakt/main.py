from . import trakt_init
from .sync import sync_letterboxd_to_trakt


def run():
    trakt_init()

    sync_letterboxd_to_trakt()


if __name__ == "__main__":
    run()
