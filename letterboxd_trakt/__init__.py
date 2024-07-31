import os

import trakt
from dotenv import load_dotenv
from trakt import core

load_dotenv()

core.AUTH_METHOD = core.DEVICE_AUTH


def init_trakt():
    trakt.init(
        client_id=os.getenv("TRAKT_CLIENT_ID"),
        client_secret=os.getenv("TRAKT_CLIENT_SECRET"),
        store=True,
    )
