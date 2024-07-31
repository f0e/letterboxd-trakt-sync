import os

from letterboxdpy import movie as LB_movie
from letterboxdpy import user as LB_user
from trakt import sync as T_sync
from trakt.movies import Movie as T_Movie

user_instance = LB_user.User(os.getenv("LETTERBOXD_USERNAME"))


def sync_letterboxd_to_trakt():
    lb_user_movies = LB_user.user_films(user_instance)["movies"]
    for lb_movie_slug, lb_user_movie in lb_user_movies.items():
        if not lb_user_movie["rating"]:
            continue

        lb_movie = LB_movie.Movie(lb_movie_slug)

        lb_imdb_id = lb_movie.imdb_link.split("/")[-2]

        trakt_search_res: list[T_Movie] = T_sync.search_by_id(lb_imdb_id, "imdb", "movie")
        if len(trakt_search_res) == 0:
            continue

        # ensure movie is correct. check imdb id again
        trakt_movies = [movie for movie in trakt_search_res if movie.imdb == lb_imdb_id]
        if len(trakt_movies) != 1:
            continue

        trakt_movie = trakt_movies[0]

        # NOTE: there seems to be some caching on trakt ratings so they don't appear instantly. this shouldn't be an issue, double-rating at worst is fine
        if lb_user_movie["rating"] != trakt_movie.rating:
            # TODO: sync rating dates (not sure how to fetch this using letterboxdpy. should use film url/activity?)
            T_sync.rate(trakt_movie, lb_user_movie["rating"])
            print(f"Added rating of {lb_user_movie["rating"]} to {trakt_movie.title}")
        else:
            print(f"Already gave the correct rating to {trakt_movie.title}")
