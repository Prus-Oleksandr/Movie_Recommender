import random
from pyexpat.errors import messages

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.views import View

from movie_recommender.forms import SetPreferencesForm, SearchPreferencesForm
from movie_recommender.models import Movie, Genre, Director, Actor

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

    if request.method == "POST":
        current_movie_id = request.POST.get("movie_id")
        if current_movie_id:
            current_movie = int(current_movie_id)
            seen_list = request.session.get("session_seen_movies", [])
            if current_movie not in seen_list:
                seen_list.append(current_movie)
                request.session["session_seen_movies"] = seen_list
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
        all_movies = list(Movie.objects.all())
        return random.sample(all_movies, min(len(all_movies), 10))

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
                all_genres.extend(movie.genres.all())
                all_directors.extend(movie.directors.all())
                all_actors.extend(movie.actors.all())

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

class ManagePreferencesView(LoginRequiredMixin, View):
    template_name = "manage_preferences.html"
    def get(self, request):
        user = User.objects.prefetch_related(
            "favorite_genres",
            "favorite_directors",
            "favorite_actors"
        ).get(id=request.user.id)

        results = []
        search_mode = request.GET.get("search_mode")

        if "query" in request.GET and "type" in request.GET:
            form = SearchPreferencesForm(request.GET)
            if form.is_valid():
                query = form.cleaned_data["query"]
                search_type = form.cleaned_data["type"]
                if search_type == "genre":
                    results = Genre.objects.filter(name__icontains=query)
                elif search_type == "actor":
                    results = Actor.objects.filter(full_name__icontains=query)
                elif search_type == "director":
                    results = Director.objects.filter(full_name__icontains=query)
        context = {
            "favorite_genres": user.favorite_genres.all(),
            "favorite_actors": user.favorite_actors.all(),
            "favorite_directors": user.favorite_directors.all(),
            "results": results,
            "search_mode": search_mode,
        }
        return render(request, self.template_name, context=context)
    def post(self, request):
        action = request.POST.get("action")
        item_id = request.POST.get("item_id")

        if not item_id or not item_id.isdigit():
            return redirect("manage_preferences")

        item_id = int(item_id)
        user = request.user

        try:
            if action == "remove_genre":
                user.favorite_genres.remove(item_id)
            elif action == "remove_actor":
                user.favorite_actors.remove(item_id)
            elif action == "remove_director":
                user.favorite_directors.remove(item_id)
            elif action == "add_genre":
                user.favorite_genres.add(item_id)
            elif action == "add_actor":
                user.favorite_actors.add(item_id)
            elif action == "add_director":
                user.favorite_directors.add(item_id)
        except ObjectDoesNotExist:
            messages.error(request, "Item does not exist")
        except ValueError:
            messages.error(request, "Invalid input")
        return redirect("manage_preferences")
