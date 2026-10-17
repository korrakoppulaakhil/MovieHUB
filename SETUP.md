# Local setup

1. Create and activate a Python virtual environment.
2. Install Django (the project was created with Django 6.1).
3. Set `DJANGO_SECRET_KEY` to a persistent, randomly generated value before
   deploying. For local development, Django generates a temporary key when
   this environment variable is not set.
4. Run database migrations with `python manage.py migrate`.
5. Start the development server with `python manage.py runserver`.

The SQLite database and environment files are local-only and are excluded from
Git.
