# Setup and deployment

## Local development

1. Create and activate a Python virtual environment.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Run migrations with `python manage.py migrate`.
4. Start the development server with `python manage.py runserver`.

For local development, Django generates a temporary secret key if
`DJANGO_SECRET_KEY` is not set.

## Deploy to Render

Create a Render **Web Service** from this repository with:

- **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate`
- **Start Command:** `gunicorn movieportal.wsgi:application`

In the Render service environment, set `DJANGO_SECRET_KEY` to a generated
secret and `DEBUG` to `false`. Attach a Render PostgreSQL database and make its
internal connection URL available to the service as `DATABASE_URL`. Render
sets `RENDER_EXTERNAL_HOSTNAME` for the service; the app uses it for allowed
hosts and HTTPS CSRF requests. If using a custom domain, add it to
`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.

The project uses WhiteNoise to serve collected static files. A local SQLite
database is used only when `DATABASE_URL` is not configured; Render's local
filesystem is ephemeral, so SQLite is not suitable for persistent production
data.
