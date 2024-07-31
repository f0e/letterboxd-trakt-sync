# Letterboxd Trakt Sync

Script to sync your Letterboxd ratings to your Trakt account.

## Usage

- Copy `.env.template` to `.env` and fill out the values
  - To obtain values for `TRAKT_CLIENT_ID` and `TRAKT_CLIENT_SECRET`, [create a Trakt application](https://trakt.tv/oauth/applications) with the following values:
    - Name: letterboxd-trakt-sync
    - Redirect URI: `urn:ietf:wg:oauth:2.0:oob`
    - Enable the /scrobble permission.
- Install the requirements: `python install -r requirements.txt`
- Run the script: `python letterboxd_trakt/main.py`
