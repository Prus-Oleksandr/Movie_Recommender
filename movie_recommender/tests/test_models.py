from django.test import TestCase
from django.contrib.auth import get_user_model
from movie_recommender.models import Movie, Genre, Actor, Director

User = get_user_model()


class UnifiedModelsTest(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name="Sci-Fi")
        self.movie1 = Movie.objects.create(
            title="Movie 1", description="D1", release_year=2000
        )
        self.movie2 = Movie.objects.create(
            title="Movie 2", description="D2", release_year=2001
        )
        self.movie3 = Movie.objects.create(
            title="Movie 3", description="D3", release_year=2002
        )

    def test_model_string_representations(self):
        self.assertEqual(str(self.genre), "Sci-Fi")
        self.assertEqual(str(self.movie1), "Movie 1(2000)")


class MovieQuerySetCustomTest(TestCase):
    def setUp(self):
        self.genre_action = Genre.objects.create(name="Action")
        self.movie_best = Movie.objects.create(
            title="Fight Club", description="Cool", release_year=1999
        )
        self.movie_best.genres.add(self.genre_action)
        self.movie_bad = Movie.objects.create(
            title="Notebook", description="Sad", release_year=2004
        )

        self.user = User.objects.create_user(
            username="moviefan", password="password123"
        )
        self.user.favorite_genres.add(self.genre_action)

    def test_recommended_for_user_filters_and_orders(self):
        queryset = Movie.objects.all().recommended_for_user(self.user, [])
        self.assertIn(self.movie_best, queryset)
        self.assertNotIn(self.movie_bad, queryset)