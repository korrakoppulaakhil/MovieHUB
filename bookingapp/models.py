import uuid
from django.db import models


# ==========================================
# CITY
# ==========================================

class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    state = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name}, {self.state}"


# ==========================================
# THEATRE
# ==========================================

class Theatre(models.Model):
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="theatres"
    )
    name = models.CharField(max_length=200)
    address = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.city.name}"


# ==========================================
# SCREEN
# ==========================================

class Screen(models.Model):
    SCREEN_TYPES = [
        ("2D", "2D"),
        ("3D", "3D"),
        ("IMAX", "IMAX"),
        ("4DX", "4DX"),
        ("DOLBY", "Dolby Atmos"),
    ]

    theatre = models.ForeignKey(
        Theatre,
        on_delete=models.CASCADE,
        related_name="screens"
    )

    name = models.CharField(max_length=100)

    screen_type = models.CharField(
        max_length=20,
        choices=SCREEN_TYPES,
        default="2D"
    )

    capacity = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("theatre", "name")

    def __str__(self):
        return f"{self.theatre.name} - {self.name}"


# ==========================================
# MOVIE
# ==========================================

class Movie(models.Model):
    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=100)

    view_count = models.PositiveBigIntegerField(default=0)

    duration = models.PositiveIntegerField(
        help_text="Duration in minutes"
    )

    release_date = models.DateField()

    # Movie booking availability dates
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Starting Date"
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Ending Date"
    )

    poster_url = models.URLField(blank=True)
    description = models.TextField()

    trailer_url = models.URLField(blank=True)
    language = models.CharField(max_length=100, blank=True)
    director = models.CharField(max_length=200, blank=True)
    cast = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return self.title


# ==========================================
# SHOWTIME
# One movie can have multiple timings/screens.
# An empty date means the showtime repeats
# throughout the movie's availability period.
# ==========================================

class Showtime(models.Model):
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="showtimes"
    )

    screen_number = models.PositiveIntegerField(default=1)

    screen = models.ForeignKey(
        Screen,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="showtimes"
    )

    # Existing date-specific showtimes are retained.
    # Leave empty for a recurring showtime.
    date = models.DateField(
        null=True,
        blank=True,
        help_text="Leave empty to use the movie's availability dates."
    )

    time = models.TimeField()

    # General ticket price retained for compatibility.
    ticket_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default="200.00"
    )

    # Seating category prices
    ground_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default="100.00"
    )

    platinum_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default="200.00"
    )

    recliner_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default="300.00"
    )

    box_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default="400.00"
    )

    def __str__(self):
        date_text = self.date or "Recurring"
        return f"{self.movie.title} - {date_text} {self.time}"


# ==========================================
# SEAT BOOKING
# ==========================================

class SeatBooking(models.Model):
    showtime = models.ForeignKey(
        Showtime,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    # Date selected by the customer
    booked_for_date = models.DateField(
        null=True,
        blank=True
    )

    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    selected_seats = models.CharField(max_length=200)

    total_paid = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    booked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.showtime}"


# ==========================================
# MOVIE REVIEW
# ==========================================

class MovieReview(models.Model):
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    reviewer_name = models.CharField(max_length=100)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.movie.title} - {self.rating}/5"


# ==========================================
# WEBSITE VISITOR TRACKING
# ==========================================

class WebsiteVisitor(models.Model):
    visitor_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    page_views = models.PositiveBigIntegerField(default=1)

    class Meta:
        ordering = ["-last_seen"]
        verbose_name = "Website Visitor"
        verbose_name_plural = "Website Visitors"

    def __str__(self):
        return f"Visitor {self.visitor_id}"