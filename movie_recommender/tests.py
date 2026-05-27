from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .forms import SetPreferencesForm
from .models import Movie, Genre, Actor, Director

User = get_user_model()


class UnifiedModelsAndFormsTest(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name="Sci-Fi")
        self.movie1 = Movie.objects.create(title="Movie 1", description="D1", release_year=2000)
        self.movie2 = Movie.objects.create(title="Movie 2", description="D2", release_year=2001)
        self.movie3 = Movie.objects.create(title="Movie 3", description="D3", release_year=2002)

    def test_model_string_representations(self):
        self.assertEqual(str(self.genre), "Sci-Fi")
        self.assertEqual(str(self.movie1), "Movie 1(2000)")

    def test_set_preferences_form_validation(self):
        valid_data = {"chosen_movies": [self.movie1.id, self.movie2.id, self.movie3.id]}
        invalid_data = {"chosen_movies": [self.movie1.id, self.movie2.id]}

        self.assertTrue(SetPreferencesForm(data=valid_data).is_valid())
        self.assertFalse(SetPreferencesForm(data=invalid_data).is_valid())


class MovieQuerySetCustomTest(TestCase):
    def setUp(self):
        self.genre_action = Genre.objects.create(name="Action")
        self.movie_best = Movie.objects.create(title="Fight Club", description="Cool", release_year=1999)
        self.movie_best.genres.add(self.genre_action)
        self.movie_bad = Movie.objects.create(title="Notebook", description="Sad", release_year=2004)

        self.user = User.objects.create_user(username="moviefan", password="password123")
        self.user.favorite_genres.add(self.genre_action)

    def test_recommended_for_user_filters_and_orders(self):
        queryset = Movie.objects.all().recommended_for_user(self.user, [])
        self.assertIn(self.movie_best, queryset)
        self.assertNotIn(self.movie_bad, queryset)


class IndexViewTest(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name="Sci-Fi")
        self.movie = Movie.objects.create(title="Movie 1", description="Desc 1", release_year=2020)
        self.movie.genres.add(self.genre)
        self.user = User.objects.create_user(username="watcher", password="password123")
        self.url = reverse("index")

    def test_index_redirects_user_without_preferences(self):
        self.client.login(username="watcher", password="password123")
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("set_preferences"))

    def test_index_post_htmx_returns_partial_template(self):
        self.user.favorite_genres.add(self.genre)
        self.client.login(username="watcher", password="password123")
        headers = {"HTTP_HX_Request": "true"}

        response = self.client.post(self.url, {"movie_id": str(self.movie.id)}, **headers)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/movie_card.html")


class SetPreferencesViewTest(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name="Sci-Fi")
        self.actor = Actor.objects.create(full_name="Keanu Reeves")
        self.director = Director.objects.create(full_name="Lana Wachowski")

        self.movies = []
        for i in range(5):
            movie = Movie.objects.create(title=f"Movie {i}", description="Desc", release_year=2000)
            movie.genres.add(self.genre)
            movie.actors.add(self.actor)
            movie.directors.add(self.director)
            self.movies.append(movie)

        self.user = User.objects.create_user(username="newuser", password="password123")
        self.url = reverse("set_preferences")

    def test_post_valid_data_updates_user_preferences(self):
        self.client.login(username="newuser", password="password123")
        selected_movies = [self.movies[0].id, self.movies[1].id, self.movies[2].id]

        response = self.client.post(self.url, {"chosen_movies": selected_movies})

        self.assertRedirects(response, reverse("index"))
        self.assertEqual(self.user.watched_movies.count(), 3)
        self.assertIn(self.genre, self.user.favorite_genres.all())


class ManagePreferencesViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="manager", password="password123")
        self.genre = Genre.objects.create(name="Action")
        self.url = reverse("manage_preferences")

    def test_get_manage_preferences_page(self):
        self.client.login(username="manager", password="password123")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "manage_preferences.html")

    def test_htmx_search_returns_partial_template(self):
        self.client.login(username="manager", password="password123")
        headers = {"HTTP_HX_Request": "true"}

        response = self.client.get(self.url, {"query": "Action", "type": "genre"}, **headers)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/search_block.html")
        self.assertIn(self.genre, response.context["results"])

    def test_htmx_post_add_genre_triggers_refresh(self):
        self.client.login(username="manager", password="password123")
        headers = {"HTTP_HX_Request": "true"}

        response = self.client.post(self.url, {"action": "add_genre", "item_id": str(self.genre.id)}, **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("HX-Refresh"), "true")
        self.assertIn(self.genre, self.user.favorite_genres.all())

    def test_htmx_post_remove_genre_returns_empty_response(self):
        self.user.favorite_genres.add(self.genre)
        self.client.login(username="manager", password="password123")
        headers = {"HTTP_HX_Request": "true"}

        response = self.client.post(self.url, {"action": "remove_genre", "item_id": str(self.genre.id)}, **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")
        self.assertNotIn(self.genre, self.user.favorite_genres.all())