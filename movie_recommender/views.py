import random

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.views import View

from movie_recommender.forms import SetPreferencesForm
from movie_recommender.models import Movie

User = get_user_model()
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
    return render(request, "index.html", context=context)

class SetPreferencesView(LoginRequiredMixin,View):
    template_name = "set_preferences.html"

    def _get_random_movie(self):
        all_movies = Movie.objects.all()
        return random.sample(all_movies(min(len(all_movies), 10)))

    def get(self, request):
        random_movies = self._get_random_movie()
        form = SetPreferencesForm()
        form.fields["chosen_movies"].queryset = Movie.objects.filter(id__in=[m.id for m in random_movies])
        movies_with_widgets = list(zip(random_movies, form["chosen_movies"]))

        context = {
            "form": form,
            "movies_with_widgets": movies_with_widgets
        }
        return render(request, self.template_name, context=context)

    def post(self, request):
        form = SetPreferencesForm(request.POST)
        form.fields["chosen_movies"].queryset = Movie.objects.prefetch_related(
            "genres",
            "directors",
            "actors"
        )
        if form.is_valid():
            chosen_movies = form.cleaned_data["chosen_movies"]
            user = request.user

            all_genres = []
            all_directors = []
            all_actors = []

            for movie in chosen_movies:
                user.watched_movies.add(movie)
                all_genres.extend(movie.genre.all())
                all_directors.extend(movie.director.all())
                all_actors.extend(movie.actor.all())

            user.favorite_genres.add(*all_genres)
            user.favorite_directors.add(*all_directors)
            user.favorite_actors.add(*all_actors)

            return redirect("index")

        random_movies = self._get_random_movie()
        form = SetPreferencesForm()
        form.fields["chosen_movies"].queryset = Movie.objects.filter(id__in=[m.id for m in random_movies])
        movies_with_widgets = list(zip(random_movies, form["chosen_movies"]))

        context = {
            "form": form,
            "movies_with_widgets": movies_with_widgets,
            "errors": form.errors.get("chosen_movies", [""])[0]
        }
        return render(request, self.template_name, context=context)

class ManagePreferencesView(View):
    template_name = "manage_preferences.html"
    pass










