from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .forms import SetPreferencesForm, SearchPreferencesForm
from .models import Movie, Genre

User = get_user_model()


class CoreModelsTest(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name="Sci-Fi")
        self.movie = Movie.objects.create(
            title="The Matrix",
            description="Reality hacker",
            release_year=1999
        )
        self.movie.genres.add(self.genre)

        self.watcher = User.objects.create_user(
            username="testuser",
            password="password123"
        )
        self.watcher.favorite_genres.add(self.genre)
        self.watcher.watched_movies.add(self.movie)

    def test_model_string_representations(self):
        self.assertEqual(str(self.genre), "Sci-Fi")
        self.assertEqual(str(self.movie), "The Matrix(1999)")
        self.assertEqual(str(self.watcher), "testuser")

    def test_watcher_relationships(self):
        self.assertIn(self.genre, self.watcher.favorite_genres.all())
        self.assertIn(self.movie, self.watcher.watched_movies.all())
        self.assertIn(self.watcher, self.genre.watchers.all())


class FormsTest(TestCase):
    def setUp(self):
        self.movie1 = Movie.objects.create(title="Movie 1", description="Desc 1", release_year=2000)
        self.movie2 = Movie.objects.create(title="Movie 2", description="Desc 2", release_year=2001)
        self.movie3 = Movie.objects.create(title="Movie 3", description="Desc 3", release_year=2002)
        self.movie4 = Movie.objects.create(title="Movie 4", description="Desc 4", release_year=2003)

    def test_search_preferences_form_valid(self):
        form_data = {"query": "Nolan", "type": "director"}
        form = SearchPreferencesForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_search_preferences_form_invalid_type(self):
        form_data = {"query": "Nolan", "type": "invalid_type"}
        form = SearchPreferencesForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("type", form.errors)

    def test_set_preferences_form_valid_range(self):
        form_data = {"chosen_movies": [self.movie1.id, self.movie2.id, self.movie3.id]}
        form = SetPreferencesForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_set_preferences_form_too_few(self):
        form_data = {"chosen_movies": [self.movie1.id, self.movie2.id]}
        form = SetPreferencesForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("chosen_movies", form.errors)

    def test_set_preferences_form_too_many(self):
        movies = [
            Movie.objects.create(title=f"M {i}", description="D", release_year=2000).id
            for i in range(8)
        ]
        form_data = {"chosen_movies": movies}
        form = SetPreferencesForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("chosen_movies", form.errors)


class IndexViewTest(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name="Sci-Fi")
        self.movie1 = Movie.objects.create(title="Movie 1", description="Desc 1", release_year=2020)
        self.movie1.genres.add(self.genre)
        self.movie2 = Movie.objects.create(title="Movie 2", description="Desc 2", release_year=2021)
        self.movie2.genres.add(self.genre)

        self.user = User.objects.create_user(username="watcher", password="password123")
        self.url = reverse("index")

    def test_index_redirects_anonymous_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_index_redirects_user_without_preferences(self):
        self.client.login(username="watcher", password="password123")
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("set_preferences"))

    def test_index_displays_recommended_movie(self):
        self.user.favorite_genres.add(self.genre)
        self.client.login(username="watcher", password="password123")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertEqual(response.context["selected_movie"], self.movie1)

    def test_index_post_adds_movie_to_session_seen_list(self):
        self.user.favorite_genres.add(self.genre)
        self.client.login(username="watcher", password="password123")

        response = self.client.post(self.url, {"movie_id": str(self.movie1.id)})
        self.assertRedirects(response, self.url)

        session = self.client.session
        self.assertIn(self.movie1.id, session["session_seen_movies"])

    def test_index_post_htmx_returns_partial_template(self):
        self.user.favorite_genres.add(self.genre)
        self.client.login(username="watcher", password="password123")

        headers = {"HTTP_HX_Request": "true"}
        response = self.client.post(self.url, {"movie_id": str(self.movie1.id)}, **headers)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/movie_card.html")
        self.assertEqual(response.context["selected_movie"], self.movie2)

    def test_index_resets_session_when_no_recommendations_left(self):
        self.user.favorite_genres.add(self.genre)
        self.client.login(username="watcher", password="password123")

        session = self.client.session
        session["session_seen_movies"] = [self.movie1.id, self.movie2.id]
        session.save()

        response = self.client.get(self.url)
        self.assertRedirects(response, self.url)

        session = self.client.session
        self.assertEqual(session["session_seen_movies"], [])