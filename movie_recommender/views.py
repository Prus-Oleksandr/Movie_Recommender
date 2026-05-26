from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.shortcuts import render, redirect
from django.views import View

from movie_recommender.models import Movie


@login_required
def index(request):
    current_user = request.user
    user_with_prefs  = User.objects.prefetch_related(
        "favorite_genres",
        "favorite_directors",
        "favorite_actors"
    ).get(pk=current_user.pk)

    if (
            not user_with_prefs.favorite_genres.exists()
            and not user_with_prefs.favorite_directors.exists()
            and not user_with_prefs.favorite_actors.exists()
    ):
        return redirect("set_preferences") #redirect to the preferences page

    if "session_seen_movies" not in request.session:
        request.session["session_seen_movies"] = []

    watched_movies_ids = user_with_prefs.watched_movies.values_list("id", flat=True)
    session_seen_movies_ids = request.session["session_seen_movies"]
    exclude_movies_ids = session_seen_movies_ids + watched_movies_ids
    available_movies = Movie.objects.exclude(id__in=exclude_movies_ids) #discard watched and skipped movies

    fav_genres_ids = user_with_prefs.favorite_genres.values_list("id", flat=True)
    fav_directors_ids = user_with_prefs.favorite_directors.values_list("id", flat=True)
    fav_actors_ids = user_with_prefs.favorite_actors.values_list("id", flat=True)

    recommended_movies = available_movies.filter(
        Q(genres__id__in=fav_genres_ids) |
        Q(actors__id__in=fav_actors_ids) |
        Q(directors__id__in=fav_directors_ids) # filter
    ).annotate(match_count=Count("genres", filter=Q(genres__id__in=fav_genres_ids)) +
                           Count("actors", filter=Q(actors__id__in=fav_actors_ids)) +
                           Count("directors", filter=Q(directors__id__in=fav_directors_ids))
    ).order_by("-match_count", "?").distinct() # sorter

    if not recommended_movies.exists():
        request.session["session_seen_movies"] = []
        request.session.modified = True
        return redirect("index")

    selected_movie = recommended_movies.first()

    if request.method == "POST" and session_seen_movies_ids:
        currrent_movie_id = request.POST.get("movie_id")
        if currrent_movie_id:
            current_movie = int(currrent_movie_id)
            if current_movie not in request.session["session_seen_movies"]:
                request.session["session_seen_movies"].append(current_movie)
                request.session.modified = True
                return redirect("index")

            context = {
                "selected_movie": selected_movie,
            }

            return render(request, "index.html", context)

class SetPreferencesView(LoginRequiredMixin,View):
    pass








