from django import forms

from movie_recommender.models import Movie


class SetPreferencesForm(forms.Form):
    chosen_movies = forms.ModelMultipleChoiceField(
        queryset=Movie.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "btn-check"}),
        required=True,
    )

    def clean_chosen_movies(self):
        chosen_movies = self.cleaned_data.get("chosen_movies")
        if chosen_movies and (len(chosen_movies) < 3 or len(chosen_movies) > 7):
            raise forms.ValidationError(
                "Please select between 3 and 7 movies"
            )
        return chosen_movies


class SearchPreferencesForm(forms.Form):
    TYPE_CHOICES = [
        ("genre", "Genre"),
        ("director", "Director"),
        ("actor", "Actor"),
    ]
    query = forms.CharField(required=True, strip=True)
    type = forms.ChoiceField(choices=TYPE_CHOICES, required=True)
