import os

import trakt
from dotenv import load_dotenv
from rich.console import Console
from trakt import core
from trakt.errors import ForbiddenException
from trakt.users import User as T_user

console = Console(highlight=False)

load_dotenv()

core.AUTH_METHOD = core.DEVICE_AUTH


def trakt_init():
    # this is pretty stupid, but i looked decently well and couldn't find 'is_logged_in' or similar? credentials should autoload when using store=True and they do, but i don't know if there's an easy way to see if they loaded successfully and are valid
    try:
        T_user("me")
        return
    except ForbiddenException:
        pass

    while True:
        try:
            res = trakt.init(
                client_id=os.getenv("TRAKT_CLIENT_ID"),
                client_secret=os.getenv("TRAKT_CLIENT_SECRET"),
                store=True,
            )

            if res.status_code == 200:
                console.print("Signed in to Trakt", style="dark_green")
                return
        except Exception:
            console.print_exception()

        console.print("Failed to initialise Trakt, try again.", style="dark_red")
