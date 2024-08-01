import datetime
import time

import humanize
from letterboxdpy import movie as LB_movie
from letterboxdpy import user as LB_user
from trakt import sync as T_sync
from trakt.movies import Movie as T_Movie
from trakt.users import User as T_user

from . import console
from .config import Account, Config

# TODO: env vars?
DRY_RUN = False
TRAKT_RATE_LIMIT = 1.5
WATCH_SEARCH_RANGE_HOURS = 48

# TODO: title matching? dangerous if inaccurate though.
# TODO: could possibly look at last activity and see if theres anything missing from there to the next thing in user_films and warn/fill in gaps?


def extract_imdb_id_from_link(imdb_link: str):
    return imdb_link.split("/")[-2]


def convert_trakt_datetime_str(rated_at: str):
    return datetime.datetime.strptime(rated_at, "%Y-%m-%dT%H:%M:%S.%fZ")


def get_trakt_movie(imdb_id: str):
    trakt_search_res: list[T_Movie] = T_sync.search_by_id(imdb_id, "imdb", "movie")
    if len(trakt_search_res) == 0:
        console.print("Couldn't find movie in Trakt. Not a movie?", style="dim dark_red")
        return False

    # ensure movie is correct. check imdb id again
    trakt_movies = [movie for movie in trakt_search_res if movie.imdb == imdb_id]
    if len(trakt_movies) != 1:
        console.print(
            "Couldn't find movie in Trakt, or multiple movies found?",
            style="dim dark_red",
        )
        return False

    return trakt_movies[0]


def get_needs_trakt_rating(
    lb_rating: int,
    lb_rating_date: datetime.date | None,
    lb_imdb_id: str,
    trakt_movie_ratings: list[T_Movie],
):
    if not lb_rating:
        console.print("Haven't rated", style="dim")
        return False

    trakt_rating = next(
        (trakt_movie for trakt_movie in trakt_movie_ratings if trakt_movie["movie"]["ids"]["imdb"] == lb_imdb_id),
        None,
    )

    if trakt_rating:
        trakt_rating_datetime = convert_trakt_datetime_str(trakt_rating["rated_at"])

        # HACK: letterboxd dates dont have a time component, just use midnight for everything. if the user manually rated on trakt just overwrite it with this, i don't care. letterboxd should be the source of truth and noone is THAT nitpicky that they care about when on a day they rated things, right? TODO: this'll be fixed probably if i add trakt->letterboxd syncing
        trakt_rating_datetime = trakt_rating_datetime.replace(hour=0, minute=0, second=0, microsecond=0)

        rating_day_is_okay = True  # NOTE: if there's no rating date then default to the day being okay. if they rated in trakt on another day then it doesn't really matter. TODO: will be fixed if i add trakt->letterboxd sync

        if lb_rating_date:
            lb_rating_datetime = datetime.datetime.combine(
                lb_rating_date, datetime.time(0, 0)
            )  # don't have the time info, just use midnight

            # NOTE: i don't care, just overwrite all dates
            # if lb_rating_date < trakt_rating_date:
            #     # trakt rating is newer. OVERRULED. might be different or the same, don't care.
            #     # TODO: if trakt->letterboxd is ever added, this'll be handled
            #     console.print("Trakt rating is newer, skipping", style="dim")
            #     return False

            rating_day_is_okay = lb_rating_datetime == trakt_rating_datetime

        if rating_day_is_okay and trakt_rating["rating"] == lb_rating:
            # rated at same time, same rating. all good
            # TODO: check if rating 'times' break this, may have to round to the day
            console.print(
                (
                    f"Trakt rating is already correct ({trakt_rating['rating']}" + f" on {humanize.naturaldate(lb_rating_date)})"
                    if lb_rating_date
                    else ""
                ),
                style="dim",
            )
            return False

        console.print(
            f"Trakt rating is outdated ({trakt_rating['rating']} at {humanize.naturaldate(trakt_rating_datetime.date())} -> {lb_rating} at {lb_rating_date})",
            style="dim red",
        )

    return True


def get_needs_trakt_watch(
    lb_imdb_id: str,
    lb_watch_date: datetime.date | None,
    trakt_movie_watches: list[T_Movie],
):
    # see if it was watched at the same time, if not, need to add it
    for trakt_movie in trakt_movie_watches:
        if trakt_movie.imdb != lb_imdb_id:
            continue

        history = T_sync.get_history("movies", trakt_movie.trakt)

        if not lb_watch_date:
            # no letterboxd watch date and it's already been watched in trakt, she'll be right. TODO: handle this if anyone cares
            return False

        lb_watch_datetime = datetime.datetime.combine(
            lb_watch_date, datetime.time(0, 0)
        )  # don't have the time info, just use midnight

        for entry in history:
            trakt_watch_datetime = convert_trakt_datetime_str(entry["watched_at"])

            # search around the area to see if it was manually added to trakt
            trakt_watch_diff = abs(lb_watch_datetime - trakt_watch_datetime)
            if trakt_watch_diff <= datetime.timedelta(hours=WATCH_SEARCH_RANGE_HOURS):
                console.print(
                    "Trakt already watched"
                    + " (manually added to Trakt, time difference from Letterboxd is {humanize.precisedelta(trakt_watch_diff)})"
                    * bool(trakt_watch_diff),  # >:)
                    style="dim",
                )
                return False

    return True


# diary - official log of stuff you watched/rated with times
# user_films - everything, no times
# activity - actual times you did things, not official necessarily. probably ok for rating dates, but not for watching stuff


def get_letterboxd_user(username: str):
    try:
        return LB_user.User(username)
    except Exception as e:
        if e.__str__() == "No user found":
            console.print("Letterboxd user not found", style="red")
            return


def sync(
    trakt_movie_watches: list[T_Movie],
    trakt_movie_ratings: list[T_Movie],
    lb_movie: LB_movie.Movie,
    lb_rating: int,
    lb_rating_date: datetime.date | None,
    lb_watched: bool,
    lb_watch_date: datetime.date | None,
):
    lb_imdb_id = extract_imdb_id_from_link(lb_movie.imdb_link)

    needs_trakt_rating = get_needs_trakt_rating(lb_rating, lb_rating_date, lb_imdb_id, trakt_movie_ratings)
    needs_trakt_watch = get_needs_trakt_watch(lb_imdb_id, lb_watch_date, trakt_movie_watches)
    if not needs_trakt_rating and not needs_trakt_watch:
        return False

    trakt_movie = get_trakt_movie(lb_imdb_id)
    if not trakt_movie:
        return False

    if needs_trakt_rating:
        if not DRY_RUN:
            T_sync.rate(trakt_movie, lb_rating, lb_rating_date)
            time.sleep(TRAKT_RATE_LIMIT)

        console.print(f"Added rating of {lb_rating} at {lb_rating_date}", style="green")

    if needs_trakt_watch:
        if not DRY_RUN:
            T_sync.add_to_history(trakt_movie, lb_watch_date)
            time.sleep(TRAKT_RATE_LIMIT)

        console.print(f"Added watch at {lb_watch_date}", style="green")

    return (needs_trakt_rating, needs_trakt_watch)


def get_diary(lb_user: LB_user.User, last_diary_entry: datetime.date | None = None):
    lb_diary_to_process: list[dict] = []

    page = 1
    while True:
        lb_page_diary_entries: dict[str, dict] = LB_user.user_diary(lb_user, page=page)["entrys"]
        if not lb_page_diary_entries:
            # reached the end.
            return lb_diary_to_process

        for entry_key, entry in lb_page_diary_entries.items():
            # convert date dict to date object
            entry["date"] = datetime.date(
                entry["date"]["year"],
                entry["date"]["month"],
                entry["date"]["day"],
            )

            if last_diary_entry:
                if entry["date"] <= last_diary_entry:
                    # reached stuff we've already processed
                    return lb_diary_to_process

            lb_diary_to_process.append(entry)

        page += 1


def sync_letterboxd_diary(config: Config, account: Account):
    lb_user = get_letterboxd_user(account.letterboxd_username)
    if not lb_user:
        return

    lb_diary_to_process = get_diary(lb_user, account.internal.last_letterboxd_diary_entry)

    console.print("Starting diary sync from Letterboxd to Trakt", style="purple4")

    if len(lb_diary_to_process) == 0:
        console.print("Nothing new to add, Trakt is already up to date", style="dim purple4")
        return

    trakt_user = T_user("me")
    trakt_movie_ratings: list[T_Movie] = trakt_user.get_ratings("movies")
    trakt_movie_watches: list[T_Movie] = trakt_user.watched_movies

    movie_cache = {}

    for i, entry in enumerate(
        reversed(lb_diary_to_process)
    ):  # iterate backwards since you can rate things multiple times on letterboxd but not on trakt, so we want the last rating to be the final one. yum.
        entry_rating = entry["actions"]["rating"]

        console.print(f"{i+1}/{len(lb_diary_to_process)}: {entry['name']} on {humanize.naturaldate(entry['date'])}")

        if entry["slug"] not in movie_cache:
            # just in case someone watches the same movie 10000 times optimisation? whatever it's no extra code
            movie_cache[entry["slug"]] = {
                "movie": LB_movie.Movie(entry["slug"]),
                "rated": False,
            }

        lb_movie = movie_cache[entry["slug"]]["movie"]

        sync(
            trakt_movie_watches,
            trakt_movie_ratings,
            lb_movie,
            entry_rating,
            entry["date"],
            True,
            entry["date"],
        )

        account.internal.last_letterboxd_diary_entry = entry["date"]
        config.save()

    console.print("Finished syncing!", style="purple4")


def full_sync_letterboxd(account: Account):
    # TODO: need to reimplement
    pass

    # lb_user = get_letterboxd_user(account.letterboxd_username)
    # if not lb_user:
    #     return

    # console.print("Starting full sync from Letterboxd to Trakt", style="purple4")

    # lb_user_movies = LB_user.user_films(lb_user)["movies"]
    # lb_user_diary = LB_user.user_diary(lb_user)

    # trakt_user = T_user("me")
    # trakt_movie_ratings: list[T_Movie] = trakt_user.get_ratings("movies")
    # trakt_movies: list[T_Movie] = trakt_user.watched_movies

    # for i, (lb_movie_slug, lb_user_movie) in enumerate(lb_user_movies.items()):
    #     console.print(f"{i+1}/{len(lb_user_movies)}: {lb_user_movie['name']}")

    #     lb_rating = lb_user_movie["rating"]
    #     lb_movie = LB_movie.Movie(lb_movie_slug)
    #     lb_imdb_id = extract_imdb_id_from_link(lb_movie.imdb_link)

    #     needs_trakt_rating = get_needs_trakt_rating(lb_rating, lb_imdb_id, trakt_movie_ratings)
    #     needs_trakt_watch = get_needs_trakt_watch(lb_imdb_id, trakt_movies)
    #     if not needs_trakt_rating and not needs_trakt_watch:
    #         continue

    # console.print("Finished syncing!", style="purple4")
