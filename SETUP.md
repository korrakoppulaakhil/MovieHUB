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

In the Render service environment, set `DJANGO_SECRET_KEY` to a persistent,
generated secret and `DEBUG` to `false`. The app accepts `SECRET_KEY` as an
alias and generates a temporary key if neither variable is present, so the
service can still start; that temporary key changes on restarts and invalidates
sessions and signed data. Attach a Render PostgreSQL database and make its
internal connection URL available to the service as `DATABASE_URL`. Render
sets `RENDER_EXTERNAL_HOSTNAME` for the service; the app uses it for allowed
hosts and HTTPS CSRF requests. If using a custom domain, add it to
`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.

The project uses WhiteNoise to serve collected static files. A local SQLite
database is used only when `DATABASE_URL` is not configured; Render's local
filesystem is ephemeral, so SQLite is not suitable for persistent production
data.

## Admin password reset email

The admin login page includes a password reset link. Reset requests only send
email to active staff accounts that have an email address. Configure an SMTP
provider in the Render web service environment so the reset email can be
delivered:

- `EMAIL_HOST`: SMTP server hostname
- `EMAIL_PORT`: SMTP port (commonly `587`)
- `EMAIL_USE_TLS`: `true` for STARTTLS (commonly used with port `587`)
- `EMAIL_HOST_USER`: SMTP account username
- `EMAIL_HOST_PASSWORD`: SMTP password or provider-issued app password
- `DEFAULT_FROM_EMAIL`: sender address accepted by the SMTP provider

Keep SMTP credentials private and enter them only in Render's environment
settings. In local development, reset emails are printed to the runserver
console by default.
