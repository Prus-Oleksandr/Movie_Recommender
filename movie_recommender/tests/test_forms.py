from django.test import TestCase
from movie_recommender.forms import SetPreferencesForm
from movie_recommender.models import Movie

class SetPreferencesFormTest(TestCase):
    def setUp(self):
        self.movie1 = Movie.objects.create(
            title="Movie 1", description="D1", release_year=2000
        )
        self.movie2 = Movie.objects.create(
            title="Movie 2", description="D2", release_year=2001
        )
        self.movie3 = Movie.objects.create(
            title="Movie 3", description="D3", release_year=2002
        )

    def test_set_preferences_form_validation(self):
        valid_data = {"chosen_movies": [self.movie1.id, self.movie2.id, self.movie3.id]}
        invalid_data = {"chosen_movies": [self.movie1.id, self.movie2.id]}

        self.assertTrue(SetPreferencesForm(data=valid_data).is_valid())
        self.assertFalse(SetPreferencesForm(data=invalid_data).is_valid())