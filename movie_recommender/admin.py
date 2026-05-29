from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Actor, Director, Genre, Movie, Watcher

@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ("full_name",)
    search_fields = ("full_name",)

@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ("full_name",)
    search_fields = ("full_name",)

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "release_year", "display_genres")
    search_fields = ("title",)
    filter_horizontal = ("genres", "directors", "actors")

    def display_genres(self, obj):
        return ", ".join([genre.name for genre in obj.genres.all()])

    display_genres.short_description = "Genres"

@admin.register(Watcher)
class WatcherAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Preferences", {
            "fields": ("favorite_genres", "favorite_directors", "favorite_actors", "watched_movies"),
        }),
    )
    filter_horizontal = ("favorite_genres", "favorite_directors", "favorite_actors", "watched_movies", "groups", "user_permissions")