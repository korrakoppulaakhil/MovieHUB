# MovieHUB

## Deploy on Render

Create a Render Web Service for this repository and use these commands:

- **Build:** `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate`
- **Start:** `gunicorn movieportal.wsgi:application`

Set `DJANGO_SECRET_KEY` and `DEBUG=false` in the service environment, and connect
a Render PostgreSQL database using `DATABASE_URL`. The app can start without a
configured key using a temporary generated key, but this invalidates sessions
and signed data on restarts; configure a persistent `DJANGO_SECRET_KEY` for
production. See [SETUP.md](SETUP.md) for details.