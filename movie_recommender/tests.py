from django.test import TestCase
from django.contrib.auth import get_user_model
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

