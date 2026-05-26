from django.contrib.auth.models import AbstractUser
from django.db import models

class Actor(models.Model):
    full_name = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.full_name

class Director(models.Model):
    full_name = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.full_name

class Genre(models.Model):
    name = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.name

class Movie(models.Model):
    title = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    release_year = models.IntegerField()
    genres = models.ManyToManyField(Genre, related_name="movies")
    directors = models.ManyToManyField(Director,  related_name="movies")
    actors = models.ManyToManyField(Actor, related_name="movies")
    poster = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.title}({str(self.release_year)})"


class Watcher(AbstractUser):
    favorite_genres = models.ManyToManyField(Genre, related_name="watchers")
    favorite_directors = models.ManyToManyField(Director, related_name="watchers")
    favorite_actors = models.ManyToManyField(Actor, related_name="watchers")
    watched_movies = models.ManyToManyField(Movie, related_name="watched_movies")

    def __str__(self):
        return self.username


