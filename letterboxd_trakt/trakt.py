import time

from trakt import core
from trakt.api import TokenAuth
from trakt.auth import config_factory, device_auth

from . import console

core.AUTH_METHOD = core.DEVICE_AUTH


def trakt_init(config, account, max_retries=5, retry_delay=5):
    trakt_config = config_factory()

    # set trakt globals
    trakt_config.CLIENT_ID = account.trakt_client_id
    trakt_config.CLIENT_SECRET = account.trakt_client_secret
    trakt_config.OAUTH_TOKEN = account.internal.trakt_oauth.token
    trakt_config.OAUTH_REFRESH = account.internal.trakt_oauth.refresh
    trakt_config.OAUTH_EXPIRES_AT = account.internal.trakt_oauth.expires_at

    try:
        client = core.api()

        auth: TokenAuth = client.auth
        auth.config = trakt_config
        _, token = auth.get_token()

        if token:
            account.internal.trakt_oauth.token = trakt_config.OAUTH_TOKEN
            account.internal.trakt_oauth.refresh = trakt_config.OAUTH_REFRESH
            account.internal.trakt_oauth.expires_at = trakt_config.OAUTH_EXPIRES_AT
            return True
    except Exception:
        console.print_exception()

    retries = 0
    while retries < max_retries:
        start = time.time()

        try:
            device_auth(config=trakt_config)

            console.print("Signed in to Trakt", style="dark_green")

            # store oauth data
            account.internal.trakt_oauth.token = trakt_config.OAUTH_TOKEN
            account.internal.trakt_oauth.refresh = trakt_config.OAUTH_REFRESH
            account.internal.trakt_oauth.expires_at = trakt_config.OAUTH_EXPIRES_AT

            config.save()

            return True
        except Exception:
            console.print_exception()

        elapsed = time.time() - start
        retries += 1
        remaining_delay = max(0, retry_delay - elapsed)

        console.print(
            f"Failed to initialise Trakt (attempt {retries}/{max_retries}), retrying in {remaining_delay:.1f} seconds...",
            style="dark_red",
        )

        time.sleep(remaining_delay)

    console.print("Max retries reached. Trakt initialization failed.", style="bold red")
    return False
