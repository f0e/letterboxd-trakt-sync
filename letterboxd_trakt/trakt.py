import trakt
from trakt import core
from trakt.errors import ForbiddenException, OAuthException
from trakt.users import User as T_user

from . import console

core.AUTH_METHOD = core.DEVICE_AUTH


def trakt_init(config, account):
    # set trakt globals
    core.CLIENT_ID = account.trakt_client_id
    core.CLIENT_SECRET = account.trakt_client_secret
    core.OAUTH_TOKEN = account.internal.trakt_oauth.token
    core.OAUTH_REFRESH = account.internal.trakt_oauth.refresh
    core.OAUTH_EXPIRES_AT = account.internal.trakt_oauth.expires_at

    # this is pretty stupid, but i looked decently well and couldn't find 'is_logged_in' or similar?
    try:
        T_user("me")
        return
    except (ForbiddenException, OAuthException):
        pass

    while True:
        try:
            res = trakt.init(
                client_id=account.trakt_client_id,
                client_secret=account.trakt_client_secret,
            )

            if res.status_code == 200:
                console.print("Signed in to Trakt", style="dark_green")

                # store oauth data
                account.internal.trakt_oauth.token = core.OAUTH_TOKEN
                account.internal.trakt_oauth.refresh = core.OAUTH_REFRESH
                account.internal.trakt_oauth.expires_at = core.OAUTH_EXPIRES_AT
                config.save()

                return
        except Exception:
            console.print_exception()

        console.print("Failed to initialise Trakt, try again.", style="dark_red")
