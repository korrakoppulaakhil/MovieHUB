from django.contrib import admin

from .models import (
    City,
    Theatre,
    Screen,
    Movie,
    Showtime,
    SeatBooking,
    MovieReview,
    WebsiteVisitor,
)


# ==========================================
# CITY ADMIN
# ==========================================

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "state", "is_active")
    list_filter = ("state", "is_active")
    search_fields = ("name", "state")


# ==========================================
# SCREEN INLINE
# ==========================================

class ScreenInline(admin.TabularInline):
    model = Screen
    extra = 1

    fields = (
        "name",
        "screen_type",
        "capacity",
        "is_active",
    )


# ==========================================
# THEATRE ADMIN
# ==========================================

@admin.register(Theatre)
class TheatreAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
        "address",
        "is_active",
    )

    list_filter = ("city", "is_active")

    search_fields = (
        "name",
        "address",
        "city__name",
    )

    inlines = [ScreenInline]


# ==========================================
# SCREEN ADMIN
# ==========================================

@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "theatre",
        "screen_type",
        "capacity",
        "is_active",
    )

    list_filter = (
        "screen_type",
        "is_active",
        "theatre",
    )

    search_fields = (
        "name",
        "theatre__name",
        "theatre__city__name",
    )


# ==========================================
# SHOWTIME INLINE
# Starting/Ending dates are NOT repeated here.
# Add multiple timings and screens per movie.
# ==========================================

class ShowtimeInline(admin.TabularInline):
    model = Showtime
    extra = 1
    show_change_link = True

    fields = (
        "time",
        "screen",
        "screen_number",
        "ticket_price",
        "ground_price",
        "platinum_price",
        "recliner_price",
        "box_price",
    )

    autocomplete_fields = ("screen",)


# ==========================================
# MOVIE REVIEW INLINE
# ==========================================

class MovieReviewInline(admin.TabularInline):
    model = MovieReview
    extra = 0

    fields = (
        "reviewer_name",
        "rating",
        "comment",
        "created_at",
    )

    readonly_fields = ("created_at",)


# ==========================================
# MOVIE ADMIN
# ==========================================

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "genre",
        "language",
        "release_date",
        "start_date",
        "end_date",
        "is_featured",
        "showtime_count",
    )

    list_filter = (
        "genre",
        "language",
        "is_featured",
    )

    search_fields = (
        "title",
        "genre",
        "language",
        "director",
        "cast",
    )

    list_editable = ("is_featured",)

    readonly_fields = (
        "view_count",
        "showtime_count",
        "tickets_booked_count",
    )

    fieldsets = (
        (
            "Movie Information",
            {
                "fields": (
                    "title",
                    "genre",
                    "language",
                    "duration",
                    "description",
                )
            },
        ),
        (
            "Movie Availability",
            {
                "description": (
                    "Set the date range once for this movie. "
                    "New showtime rows will use this availability period."
                ),
                "fields": (
                    "release_date",
                    "start_date",
                    "end_date",
                ),
            },
        ),
        (
            "Poster and Trailer",
            {
                "fields": (
                    "poster_url",
                    "trailer_url",
                )
            },
        ),
        (
            "Additional Information",
            {
                "fields": (
                    "director",
                    "cast",
                    "is_featured",
                )
            },
        ),
        (
            "Movie Statistics",
            {
                "fields": (
                    "view_count",
                    "showtime_count",
                    "tickets_booked_count",
                )
            },
        ),
    )

    inlines = [
        ShowtimeInline,
        MovieReviewInline,
    ]

    @admin.display(description="Showtimes")
    def showtime_count(self, obj):
        return obj.showtimes.count()

    @admin.display(description="Bookings")
    def tickets_booked_count(self, obj):
        return SeatBooking.objects.filter(
            showtime__movie=obj
        ).count()


# ==========================================
# SHOWTIME ADMIN
# ==========================================

@admin.register(Showtime)
class ShowtimeAdmin(admin.ModelAdmin):
    list_display = (
        "movie",
        "date",
        "time",
        "screen",
        "screen_number",
        "ticket_price",
        "ground_price",
        "platinum_price",
        "recliner_price",
        "box_price",
    )

    list_filter = (
        "date",
        "screen",
    )

    search_fields = (
        "movie__title",
        "screen__name",
        "screen__theatre__name",
    )

    autocomplete_fields = (
        "movie",
        "screen",
    )


# ==========================================
# SEAT BOOKING ADMIN
# ==========================================

@admin.register(SeatBooking)
class SeatBookingAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name",
        "customer_email",
        "showtime",
        "booked_for_date",
        "selected_seats",
        "total_paid",
        "booked_at",
    )

    list_filter = (
        "booked_for_date",
        "booked_at",
    )

    search_fields = (
        "customer_name",
        "customer_email",
        "showtime__movie__title",
    )

    readonly_fields = ("booked_at",)


# ==========================================
# MOVIE REVIEW ADMIN
# ==========================================

@admin.register(MovieReview)
class MovieReviewAdmin(admin.ModelAdmin):
    list_display = (
        "movie",
        "reviewer_name",
        "rating",
        "created_at",
    )

    list_filter = (
        "rating",
        "created_at",
    )

    search_fields = (
        "movie__title",
        "reviewer_name",
        "comment",
    )

    readonly_fields = ("created_at",)


# ==========================================
# WEBSITE VISITOR ADMIN
# ==========================================

@admin.register(WebsiteVisitor)
class WebsiteVisitorAdmin(admin.ModelAdmin):
    list_display = (
        "visitor_id",
        "first_seen",
        "last_seen",
        "page_views",
    )

    list_filter = (
        "first_seen",
        "last_seen",
    )

    search_fields = ("visitor_id",)

    readonly_fields = (
        "visitor_id",
        "first_seen",
        "last_seen",
        "page_views",
    )