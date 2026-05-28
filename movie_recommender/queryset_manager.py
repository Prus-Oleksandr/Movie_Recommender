from django.db import models
from django.db.models import Q, Count, F


class MovieQuerySet(models.QuerySet):

    def available_for_user(self, user, session_seen_movies):
        watched_movies_ids = user.watched_movies.values_list(
            "id", flat=True
        )

        excluded_ids = list(watched_movies_ids) + session_seen_movies

        return self.exclude(id__in=excluded_ids)

    def recommended_for_user(self, user, session_seen_movies):
        fav_genres_ids = user.favorite_genres.values_list("id", flat=True)
        fav_actors_ids = user.favorite_actors.values_list("id", flat=True)
        fav_directors_ids = user.favorite_directors.values_list("id", flat=True)

        return (
            self.available_for_user(user, session_seen_movies)
            .filter(
                Q(genres__id__in=fav_genres_ids)
                | Q(actors__id__in=fav_actors_ids)
                | Q(directors__id__in=fav_directors_ids)
            )
            .annotate(
                genres_matches=Count(
                    "genres",
                    filter=Q(genres__id__in=fav_genres_ids),
                    distinct=True,
                ),
                actors_matches=Count(
                    "actors",
                    filter=Q(actors__id__in=fav_actors_ids),
                    distinct=True,
                ),
                directors_matches=Count(
                    "directors",
                    filter=Q(directors__id__in=fav_directors_ids),
                    distinct=True,
                ),
            )
            .annotate(
                total_matches=(
                    F("genres_matches")
                    + F("actors_matches")
                    + F("directors_matches")
                )
            )
            .order_by("-total_matches", "?")
            .distinct()
        )
