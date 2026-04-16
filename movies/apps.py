from django.apps import AppConfig
from django.conf import settings


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
