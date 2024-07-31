# Letterboxd Trakt Sync

Script to sync your Letterboxd ratings to your Trakt account.

## Usage (Manual)

- Install the requirements: `python install -r requirements.txt`
- Run the script: `python letterboxd_trakt/main.py`
- This will generate a template config at `config.yml`, you need to fill in the values.
  - To obtain values for `trakt_client_id` and `trakt_client_secret`, [create a Trakt application](https://trakt.tv/oauth/applications) with the following values:
    - Name: letterboxd-trakt-sync
    - Redirect URI: `urn:ietf:wg:oauth:2.0:oob`
    - Enable the /scrobble permission.
  - Leave the trakt_oauth values as null, these will be populated by the script.

## Usage (Docker)

You will need to view the docker logs whenever adding new accounts to your config and authorise the Trakt application.

### cli

```sh
docker run --rm \
    --name letterboxd-trakt-sync \
    -e RUN_ONCE=true \
    -v /<host_folder_config>:/config \
    ghcr.io/f0e/letterboxd-trakt-sync:latest
```

### compose

```yml
services:
  caddy:
    container_name: letterboxd-trakt-sync
    image: ghcr.io/f0e/letterboxd-trakt-sync:latest
    environment:
      - RUN_ONCE=true
    volumes:
      - /<host_folder_config>:/config
```

### Optional environment variables

- `RUN_ONCE`: set to `true` to run the script immediately on container start.
- `CRON_SCHEDULE`: sets the cron schedule for running the script (default: "0 */12* **")
