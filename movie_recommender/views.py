from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.shortcuts import render, redirect
from django.views import View

from movie_recommender.models import Movie
from movie_recommender.queryset_manager import MovieQuerySet


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

    session_seen_movies_ids = request.session["session_seen_movies"]

    if request.method == "POST" and session_seen_movies_ids:
        currrent_movie_id = request.POST.get("movie_id")
        if currrent_movie_id:
            current_movie = int(currrent_movie_id)
            if current_movie not in request.session["session_seen_movies"]:
                request.session["session_seen_movies"].append(current_movie)
                request.session.modified = True
                return redirect("index")

    recommended_movies = Movie.objects.recommended_for_user(user_with_prefs,request.session["session_seen_movies"])

    if not recommended_movies.exists():
        request.session["session_seen_movies"] = []
        request.session.modified = True
        return redirect("index")

    context = {
        "selected_movie": recommended_movies.first(),
    }
    return render(request, "index.html", context)

class SetPreferencesView(LoginRequiredMixin,View):









