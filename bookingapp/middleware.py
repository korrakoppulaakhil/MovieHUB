import uuid

from django.db.models import F
from django.utils import timezone

from .models import WebsiteVisitor


class WebsiteVisitorMiddleware:
    """
    Track unique browser visitors and public HTML page views.

    Excludes Django Admin, static files, media files,
    failed responses, and visits from logged-in staff.
    """

    COOKIE_NAME = "moviehub_visitor_id"
    COOKIE_MAX_AGE = 60 * 60 * 24 * 365

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request normally.
        response = self.get_response(request)


        # Count only successful public HTML pages requested with GET.
        if request.method != "GET":
            return response

        if response.status_code >= 400:
            return response

        # Exclude administration, assets, and media.
        excluded_paths = (
            "/admin",
            "/static/",
            "/media/",
            "/favicon.ico",
        )

        if (
            request.path == "/admin"
            or request.path.startswith(excluded_paths)
        ):
            return response

        # Ignore responses that are not HTML.
        content_type = response.get("Content-Type", "")

        if "text/html" not in content_type.lower():
            return response

        # Read the visitor ID from the browser cookie.
        cookie_value = request.COOKIES.get(self.COOKIE_NAME)

        try:
            visitor_id = (
                uuid.UUID(cookie_value)
                if cookie_value
                else uuid.uuid4()
            )
        except (ValueError, TypeError, AttributeError):
            visitor_id = uuid.uuid4()
            cookie_value = None

        # Record a new browser visitor or update an existing visitor.
        visitor, created = WebsiteVisitor.objects.get_or_create(
            visitor_id=visitor_id,
            defaults={
                "page_views": 1,
            },
        )

        if not created:
            WebsiteVisitor.objects.filter(
                pk=visitor.pk
            ).update(
                page_views=F("page_views") + 1,
                last_seen=timezone.now(),
            )

        # Store the visitor ID in the browser for future visits.
        if not cookie_value:
            response.set_cookie(
                self.COOKIE_NAME,
                str(visitor_id),
                max_age=self.COOKIE_MAX_AGE,
                httponly=True,
                secure=request.is_secure(),
                samesite="Lax",
                path="/",
            )

        return response