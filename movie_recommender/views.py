import random

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import View

from movie_recommender.forms import SetPreferencesForm, SearchPreferencesForm
from movie_recommender.models import Movie, Genre, Director, Actor

User = get_user_model()

"""
Displays a personalized movie recommendation based on user preferences.
Uses a custom manager to select a movie that matches the user's favorite 
genres, actors, and directors. It tracks previously skipped or viewed movies 
within the session, passing their IDs to the manager to exclude them from 
recommendations.
"""
@login_required
def index(request):
    """
    Displays the main page and a personalized movie recommendation.
    Uses a custom manager to select a movie that matches the user's favorite
    genres, actors, and directors. It tracks previously skipped or viewed movies
    within the session, passing their IDs to the manager to exclude them from
    recommendations. If all recommendations are exhausted, the session history
    is reset to loop the suggestions from the beginning.
    """
    current_user = request.user
    user_with_prefs = User.objects.prefetch_related(
        "favorite_genres",
        "favorite_directors",
        "favorite_actors"
    ).get(pk=current_user.pk)

    # Redirect users without any preferences to the initial setup page
    if (
            not user_with_prefs.favorite_genres.exists()
            and not user_with_prefs.favorite_directors.exists()
            and not user_with_prefs.favorite_directors.exists()
    ):
        return redirect("set_preferences")

    if "session_seen_movies" not in request.session:
        request.session["session_seen_movies"] = []

    # Handle POST request to update session with skipped movie
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

    # Centralized recommendation logic for both initial load and HTMX partials
    recommended_movies = Movie.objects.recommended_for_user(
        user_with_prefs,
        request.session["session_seen_movies"]
    )

    # Reset session history if no movies are left to recommend
    if not recommended_movies.exists():
        request.session["session_seen_movies"] = []
        request.session.modified = True
        recommended_movies = Movie.objects.recommended_for_user(user_with_prefs, [])

    context = {
        "selected_movie": recommended_movies.first(),
    }

    # Handle HTMX partial updates for smooth, page-refresh-free movie skipping.
    if request.headers.get("HX-Request"):
        return render(request, "partials/movie_card.html", context=context)

    return render(request, "index.html", context=context)


"""
Displays a list of 10 random movies for the user to select their favorites.
The GET request renders a form containing these movies. Upon submission, the 
POST request processes the chosen selection, extracts associated metadata 
(genres, actors, and directors), and saves these attributes to the user's profile 
to build their personal preferences.
"""
class SetPreferencesView(LoginRequiredMixin, View):
    template_name = "set_preferences.html"

    def _get_random_movie(self):
        watched_ids = self.request.user.watched_movies.values_list('id', flat=True)
        random_movies = Movie.objects.exclude(id__in=watched_ids).order_by('?')[:10]
        return random_movies

    def _get_form_context(self, form=None):
        """Helper to prepare the form and random movie selection for the template."""
        random_movies = self._get_random_movie()
        if not form:
            form = SetPreferencesForm()

        # Set the queryset to only include the randomly selected movies
        form.fields["chosen_movies"].queryset = Movie.objects.filter(
            id__in=[m.id for m in random_movies]
        )

        # Connect movies to widgets for the template
        movies_with_widgets = list(zip(random_movies, form["chosen_movies"]))

        return {
            "form": form,
            "movies_with_widgets": movies_with_widgets,
            "errors": form.errors.get("chosen_movies", [""])[0] if form.errors else ""
        }

    def get(self, request):
        return render(request, self.template_name, context=self._get_form_context())

    def post(self, request):
        form = SetPreferencesForm(request.POST)

        # Allow the form to validate against all movies that could have been selected
        form.fields["chosen_movies"].queryset = Movie.objects.all()

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

        # If invalid, pass the form with errors back to the context helper
        return render(request, self.template_name, context=self._get_form_context(form=form))

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
            "sections": [
                {"title": "Favorite Genres", "type": "genre", "items": user.favorite_genres.all()},
                {"title": "Favorite Actors", "type": "actor", "items": user.favorite_actors.all()},
                {"title": "Favorite Directors", "type": "director", "items": user.favorite_directors.all()},
            ],
            "results": results,
            "search_mode": search_mode,
        }

        if request.headers.get("HX-Request"):
            return render(request, "partials/search_block.html", context=context)

        return render(request, self.template_name, context=context)

    def post(self, request):
        action = request.POST.get("action")
        item_id = request.POST.get("item_id")

        if not item_id or not item_id.isdigit():
            return redirect("manage_preferences")

        item_id = int(item_id)
        user: User = request.user

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

        except (ObjectDoesNotExist, ValueError):
            if request.headers.get("HX-Request"):
                return HttpResponse("Помилка", status=400)
            return redirect("manage_preferences")

        if request.headers.get("HX-Request"):
            if "remove" in action:
                return HttpResponse("")

            response = HttpResponse("")
            response["HX-Refresh"] = "true"
            return response

        return redirect("manage_preferences")