import os
from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel

from . import console

CFG_PATH = (
    Path("/config/config.yml") if os.getenv("IN_DOCKER", False) else Path("config.yml")
)
CFG_PATH.parent.mkdir(parents=True, exist_ok=True)


class PrettyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


class TraktOAuth(BaseModel):
    token: str | None = None
    refresh: str | None = None
    expires_at: int | None = None


class AccountInternal(BaseModel):
    trakt_oauth: TraktOAuth = TraktOAuth()
    last_letterboxd_diary_entry: date | None = None


class Account(BaseModel):
    letterboxd_username: str
    trakt_client_id: str
    trakt_client_secret: str
    internal: AccountInternal = AccountInternal()


class Config(BaseModel):
    accounts: list[Account] = []

    def dump(self):
        return self.model_dump()

    def save(self, path: Path = CFG_PATH):
        with path.open("w") as f:
            yaml.dump(self.dump(), f, Dumper=PrettyDumper, sort_keys=False)

    @staticmethod
    def load(path: Path = CFG_PATH):
        if not path.exists():
            template_config = Config()
            template_config.accounts.append(
                Account(
                    letterboxd_username="your_letterboxd_username",
                    trakt_client_id="your_trakt_client_id",
                    trakt_client_secret="your_trakt_client_secret",
                )
            )
            template_config.save()

            console.print("Config not found, created template", style="orange4")
            return None

        with path.open("r") as f:
            yaml_data = yaml.safe_load(f)

            if not isinstance(yaml_data, dict):
                console.print(
                    "Failed to load config: invalid config schema", style="red"
                )
                return None

            return Config(**yaml_data)


def load_config() -> Config | None:
    try:
        config = Config.load()
        if not config:
            return None

        # filter out template accounts
        config.accounts = [
            account
            for account in config.accounts
            if account.trakt_client_id != "your_trakt_client_id"
            and account.trakt_client_secret != "your_trakt_client_secret"
        ]

        return config
    except Exception:
        console.print_exception()

    return None
