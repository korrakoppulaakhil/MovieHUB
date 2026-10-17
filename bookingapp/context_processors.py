from django.db.models import Sum

from .models import Movie, WebsiteVisitor


def moviehub_visitor_stats(request):

    # Display these statistics only on the admin dashboard.
    if request.path.rstrip("/") != "/admin":
        return {}

    # Only staff users should receive dashboard statistics.
    if not request.user.is_authenticated or not request.user.is_staff:
        return {}

    # Calculate visitor statistics.
    stats = WebsiteVisitor.objects.aggregate(
        total_page_views=Sum("page_views")
    )

    # Send visitor statistics and movie data to the dashboard.
    return {
        "moviehub_unique_visitors": WebsiteVisitor.objects.count(),
        "moviehub_total_page_views": stats["total_page_views"] or 0,
        "moviehub_movies": Movie.objects.order_by("-id")[:10],
        "moviehub_movie_count": Movie.objects.count(),
    }