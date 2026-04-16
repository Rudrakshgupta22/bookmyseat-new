from datetime import date, timedelta, datetime

from django.apps import AppConfig
from django.conf import settings
from django.db.utils import OperationalError
from django.utils import timezone


def seed_sample_movies():
    from .models import Genre, Language, Movie, Theater
    from datetime import datetime
    
    if Movie.objects.exists():
        return
    
    # Real movie data from your local database
    real_movies_data = [
        {
            "name": "avengers",
            "rating": 8.9,
            "cast": "rdj,steve,chris",
            "description": "Earth's mightiest heroes must come together and learn to fight as a team if they are going to stop the mischievous Loki and his alien army from enslaving ...",
            "release_date": None,
            "duration": None,
            "trailer_url": "https://youtu.be/TcMBFSGVi1c?si=_L4AVg2qo4qz284H",
            "genres": ["Action", "Sci-FI"],
            "languages": ["English", "Hindi"],
            "theaters": [
                {
                    "name": "rdj",
                    "time": "2024-10-31T21:09:53+00:00"
                }
            ]
        },
        {
            "name": "Ready or Not",
            "rating": 6.7,
            "cast": "dve rg erg rge ger",
            "description": "erg erg erge ger geg",
            "release_date": None,
            "duration": None,
            "trailer_url": "https://youtu.be/ZtYTwUxhAoI?si=eNyhUqvXusAVLJ3-",
            "genres": ["Horror"],
            "languages": ["English"],
            "theaters": [
                {
                    "name": "hjukuyku",
                    "time": "2024-10-23T06:00:00+00:00"
                }
            ]
        },
        {
            "name": "One Day",
            "rating": 7.0,
            "cast": "efwefwef",
            "description": "wefwefwef",
            "release_date": None,
            "duration": None,
            "trailer_url": "https://youtu.be/9dS5jr7rVdM?si=tkGtXBarVNnpb2__",
            "genres": ["Romance"],
            "languages": ["English"],
            "theaters": [
                {
                    "name": "faea",
                    "time": "2024-10-21T12:00:00+00:00"
                }
            ]
        },
        {
            "name": "Toy Story",
            "rating": 8.0,
            "cast": "adcwefwe",
            "description": "fwefwefewfwe",
            "release_date": None,
            "duration": None,
            "trailer_url": "https://youtu.be/v-PjgYDrg70?si=7okXByjgGP73d4r0",
            "genres": ["Comedy"],
            "languages": ["English", "Hindi"],
            "theaters": []
        },
        {
            "name": "Rahu Ketu",
            "rating": 6.9,
            "cast": "tujtyjyh",
            "description": "trhrthrthjr",
            "release_date": None,
            "duration": None,
            "trailer_url": "https://youtu.be/IBnkWkiDFTQ?si=Kkn7U_sntnhCbHr7",
            "genres": ["Comedy"],
            "languages": ["Hindi"],
            "theaters": []
        }
    ]
    
    # Create genres and languages
    genre_objects = {}
    language_objects = {}
    
    for movie_data in real_movies_data:
        for genre_name in movie_data['genres']:
            if genre_name not in genre_objects:
                genre_objects[genre_name], _ = Genre.objects.get_or_create(name=genre_name)
        
        for lang_name in movie_data['languages']:
            if lang_name not in language_objects:
                language_objects[lang_name], _ = Language.objects.get_or_create(
                    name=lang_name, 
                    defaults={'code': lang_name[:2].lower()}
                )
    
    # Create movies and theaters
    for movie_data in real_movies_data:
        movie = Movie.objects.create(
            name=movie_data['name'],
            rating=movie_data['rating'],
            cast=movie_data['cast'],
            description=movie_data['description'],
            release_date=movie_data['release_date'],
            duration=movie_data['duration'],
            trailer_url=movie_data['trailer_url'],
            image='',  # No image file, will use placeholder
        )
        
        # Set many-to-many relationships
        movie.genres.set([genre_objects[name] for name in movie_data['genres']])
        movie.languages.set([language_objects[name] for name in movie_data['languages']])
        
        # Create theaters
        for theater_data in movie_data['theaters']:
            Theater.objects.create(
                name=theater_data['name'],
                movie=movie,
                time=datetime.fromisoformat(theater_data['time'])
            )
def should_start_email_worker():
    import os
    import sys

    if os.environ.get('VERCEL') == '1':
        return False

    blocked_commands = {
        'makemigrations', 'migrate', 'collectstatic', 'shell', 'dbshell',
        'test', 'check', 'help', 'version', 'show_urls'
    }
    current_command = sys.argv[1] if len(sys.argv) > 1 else ''

    if current_command in blocked_commands:
        return False

    if settings.DEBUG:
        return current_command == 'runserver' and os.environ.get('RUN_MAIN') == 'true'

    return current_command in {'runserver', 'gunicorn', 'uwsgi', 'daphne', 'hypercorn', 'uvicorn'}


class MoviesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'movies'

    def ready(self):
        if getattr(settings, 'EMAIL_QUEUE_AUTOSTART', True) and should_start_email_worker():
            from .email_queue import start_email_worker

            start_email_worker()

        if getattr(settings, 'SEAT_RESERVATION_AUTOSTART', True) and should_start_email_worker():
            from .reservation_worker import start_reservation_cleanup_worker

            start_reservation_cleanup_worker()

        try:
            seed_sample_movies()
        except OperationalError:
            # Database is not ready yet (migrations may still be running)
            pass
