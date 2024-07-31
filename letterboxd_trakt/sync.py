import os

from letterboxdpy import movie as LB_movie
from letterboxdpy import user as LB_user
from trakt import sync as T_sync
from trakt.movies import Movie as T_Movie
from trakt.users import User as T_user

from . import console

# TODO: title matching? dangerous if inaccurate though.
# TODO: monitor activity on letterboxd to avoid full scans?


def sync_letterboxd_to_trakt():
    console.print("Syncing ratings from Letterboxd to Trakt", style="purple4")

    lb_user = LB_user.User(os.getenv("LETTERBOXD_USERNAME"))
    trakt_user = T_user("me")

    trakt_movie_ratings: list[T_Movie] = trakt_user.get_ratings("movies")

    lb_user_movies = LB_user.user_films(lb_user)["movies"]
    lb_rated_user_movies = [
        (lb_movie_slug, lb_user_movie) for (lb_movie_slug, lb_user_movie) in lb_user_movies.items() if lb_user_movie["rating"]
    ]

    num_lb_user_movies = len(lb_rated_user_movies)

    for i, (lb_movie_slug, lb_user_movie) in enumerate(lb_rated_user_movies):
        console.print(f"{i+1}/{num_lb_user_movies}: {lb_user_movie["name"]}")

        lb_movie = LB_movie.Movie(lb_movie_slug)

        lb_imdb_id = lb_movie.imdb_link.split("/")[-2]

        trakt_rating_index = next(
            (i for i, obj in enumerate(trakt_movie_ratings) if obj["movie"]["ids"]["imdb"] == lb_imdb_id), None
        )
        if trakt_rating_index is not None:
            trakt_rating = trakt_movie_ratings.pop(trakt_rating_index)
            if trakt_rating["rating"] == lb_user_movie["rating"]:
                console.print(f"Trakt rating is already correct ({trakt_rating['rating']})", style="dim")
                continue

            console.print(f"Trakt rating is outdated ({trakt_rating['rating']} -> {lb_user_movie['rating']})", style="dim red")

        trakt_search_res: list[T_Movie] = T_sync.search_by_id(lb_imdb_id, "imdb", "movie")
        if len(trakt_search_res) == 0:
            console.print("Couldn't find movie in Trakt. Not a movie?", style="dim dark_red")
            continue

        # ensure movie is correct. check imdb id again
        trakt_movies = [movie for movie in trakt_search_res if movie.imdb == lb_imdb_id]
        if len(trakt_movies) != 1:
            console.print("Couldn't find movie in Trakt, or multiple movies found?", style="dim dark_red")
            continue

        trakt_movie = trakt_movies[0]

        # TODO: sync rating dates (not sure how to fetch this using letterboxdpy. should use film url/activity?)
        T_sync.rate(trakt_movie, lb_user_movie["rating"])
        console.print(f"Added rating of {lb_user_movie["rating"]}", style="green")

    console.print("Finished syncing ratings.", style="purple4")
