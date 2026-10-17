from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Avg, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import (
    City,
    Theatre,
    Screen,
    Movie,
    Showtime,
    SeatBooking,
    MovieReview,
)


# =========================================================
# DEMO DATA
# =========================================================

def create_demo_data():
    """
    Create demonstration records only if no movies exist.
    Existing records are never deleted.
    """

    if Movie.objects.exists():
        return

    today = timezone.localdate()
    ending_date = today + timedelta(days=29)

    movie_data = [
        {
            "title": "RRR",
            "genre": "Action",
            "duration": 187,
            "language": "Telugu",
            "director": "S. S. Rajamouli",
            "description": (
                "Two revolutionaries take different paths "
                "and form an extraordinary friendship."
            ),
        },
        {
            "title": "Salaar",
            "genre": "Action",
            "duration": 175,
            "language": "Telugu",
            "director": "Prashanth Neel",
            "description": (
                "A powerful action drama about friendship, "
                "loyalty, and rival powers."
            ),
        },
        {
            "title": "Kalki 2898 AD",
            "genre": "Sci-Fi",
            "duration": 181,
            "language": "Telugu",
            "director": "Nag Ashwin",
            "description": (
                "A science-fiction adventure inspired "
                "by Indian mythology."
            ),
        },
        {
            "title": "Hi Nanna",
            "genre": "Drama",
            "duration": 155,
            "language": "Telugu",
            "director": "Shouryuv",
            "description": (
                "An emotional family drama about love "
                "and relationships."
            ),
        },
        {
            "title": "Hanu-Man",
            "genre": "Fantasy",
            "duration": 158,
            "language": "Telugu",
            "director": "Prasanth Varma",
            "description": (
                "A young man discovers extraordinary powers."
            ),
        },
    ]

    for item in movie_data:
        Movie.objects.create(
            title=item["title"],
            genre=item["genre"],
            duration=item["duration"],
            release_date=today,
            start_date=today,
            end_date=ending_date,
            description=item["description"],
            language=item["language"],
            director=item["director"],
            is_featured=True,
        )

    city, _ = City.objects.get_or_create(
        name="Vijayawada",
        defaults={
            "state": "Andhra Pradesh",
            "is_active": True,
        },
    )

    theatre, _ = Theatre.objects.get_or_create(
        city=city,
        name="MovieHub Cinema",
        defaults={
            "address": "Vijayawada, Andhra Pradesh",
            "is_active": True,
        },
    )

    screen1, _ = Screen.objects.get_or_create(
        theatre=theatre,
        name="Screen 1",
        defaults={
            "screen_type": "2D",
            "capacity": 100,
            "is_active": True,
        },
    )

    screen2, _ = Screen.objects.get_or_create(
        theatre=theatre,
        name="Screen 2",
        defaults={
            "screen_type": "2D",
            "capacity": 100,
            "is_active": True,
        },
    )

    screens = [screen1, screen2]

    demo_times = [
        time(10, 0),
        time(13, 30),
        time(17, 0),
        time(20, 30),
    ]

    for movie in Movie.objects.all():
        for index, show_time in enumerate(demo_times):
            screen = screens[index % len(screens)]

            Showtime.objects.get_or_create(
                movie=movie,
                screen=screen,
                date=None,
                time=show_time,
                defaults={
                    "screen_number": index % 2 + 1,
                    "ticket_price": Decimal("200.00"),
                    "ground_price": Decimal("100.00"),
                    "platinum_price": Decimal("200.00"),
                    "recliner_price": Decimal("300.00"),
                    "box_price": Decimal("400.00"),
                },
            )


# =========================================================
# DATE HELPERS
# =========================================================

def get_date_options(movie=None):
    """
    Generate a rolling 30-day calendar.

    If a movie is supplied, restrict the calendar to that
    movie's Starting Date and Ending Date.
    """

    today = timezone.localdate()

    first_date = today
    last_date = today + timedelta(days=29)

    if movie is not None:
        if movie.start_date and movie.start_date > first_date:
            first_date = movie.start_date

        if movie.end_date and movie.end_date < last_date:
            last_date = movie.end_date

    if first_date > last_date:
        return []

    options = []

    current_date = first_date

    while current_date <= last_date:
        options.append({
            "date": current_date,
            "label": current_date.strftime("%a"),
            "day": current_date.strftime("%d"),
            "month": current_date.strftime("%b"),
        })

        current_date += timedelta(days=1)

    return options


def get_selected_date(request, movie=None):
    """
    Read a requested date and ensure that it falls within
    the permitted rolling calendar and movie availability.
    """

    options = get_date_options(movie)

    if not options:
        return timezone.localdate()

    valid_dates = {
        option["date"]
        for option in options
    }

    requested_date = (
        request.POST.get("booked_for_date")
        or request.GET.get("date")
        or ""
    )

    if requested_date:
        try:
            parsed_date = date.fromisoformat(requested_date)

            if parsed_date in valid_dates:
                return parsed_date

        except (ValueError, TypeError):
            pass

    return options[0]["date"]


def movie_is_available(movie, selected_date):
    """
    Check the movie's configured availability period.
    Empty dates mean that no corresponding date limit
    has been configured.
    """

    if movie.start_date and selected_date < movie.start_date:
        return False

    if movie.end_date and selected_date > movie.end_date:
        return False

    return True


def requested_booking_date(request, showtime):
    """
    Resolve the date selected by the customer.

    A date-specific showtime can only be booked for that date.
    A recurring showtime can be booked on permitted movie dates.
    """

    movie = showtime.movie

    raw_date = (
        request.POST.get("booked_for_date")
        or request.GET.get("date")
        or ""
    )

    if raw_date:
        try:
            selected_date = date.fromisoformat(raw_date)
        except (ValueError, TypeError):
            return None
    elif showtime.date is not None:
        selected_date = showtime.date
    else:
        selected_date = get_selected_date(request, movie)

    # Existing date-specific shows retain their fixed date.
    if showtime.date is not None:
        if selected_date != showtime.date:
            return None

    # Must be within both the rolling calendar and movie range.
    valid_dates = {
        option["date"]
        for option in get_date_options(movie)
    }

    if selected_date not in valid_dates:
        return None

    if not movie_is_available(movie, selected_date):
        return None

    return selected_date


# =========================================================
# SEAT AVAILABILITY HELPERS
# =========================================================

def get_booked_seat_names(showtime, selected_date):
    """
    Find seats booked for a particular showtime and date.

    Recurring showtimes keep their bookings separate by date.
    Old bookings without a recorded booking date remain counted
    for their existing date-specific showtimes.
    """

    bookings = SeatBooking.objects.filter(
        showtime=showtime
    )

    if showtime.date is not None:
        bookings = bookings.filter(
            Q(booked_for_date=selected_date)
            | Q(booked_for_date__isnull=True)
        )
    else:
        bookings = bookings.filter(
            booked_for_date=selected_date
        )

    booked_seats = set()

    for booking in bookings:
        for seat in (booking.selected_seats or "").split(","):
            seat = seat.strip()

            if seat:
                booked_seats.add(seat)

    return booked_seats


def get_seat_sections(showtime):
    """
    Build seat sections and prices from this show's
    configured category prices.
    """

    seat_categories = [
        ("G", "Ground", 50, "ground_price"),
        ("P", "Platinum", 80, "platinum_price"),
        ("R", "Recliner", 20, "recliner_price"),
        ("B", "Box", 10, "box_price"),
    ]

    seat_sections = []
    all_seats = []
    seat_prices = {}

    for prefix, section_name, count, price_field in seat_categories:
        price = getattr(
            showtime,
            price_field,
            showtime.ticket_price,
        )

        seats = []

        for number in range(1, count + 1):
            seat_name = f"{prefix}{number:02d}"

            seats.append({
                "name": seat_name,
                "price": price,
            })

            all_seats.append(seat_name)
            seat_prices[seat_name] = price

        seat_sections.append({
            "prefix": prefix,
            "name": section_name,
            "price": price,
            "seats": seats,
        })

    return seat_sections, all_seats, seat_prices


def add_starting_prices(showtimes):
    """
    Add a lowest-category-price attribute for display
    in the movie and showtime lists.
    """

    for showtime in showtimes:
        prices = [
            showtime.ground_price,
            showtime.platinum_price,
            showtime.recliner_price,
            showtime.box_price,
        ]

        showtime.starting_price = min(prices)


# =========================================================
# HOME PAGE
# =========================================================

def home(request):
    create_demo_data()

    selected_date = get_selected_date(request)

    search_query = request.GET.get("q", "").strip()
    selected_genre = request.GET.get("genre", "").strip()
    selected_language = request.GET.get("language", "").strip()

    movies = Movie.objects.all().order_by(
        "-is_featured",
        "title",
    )

    if search_query:
        movies = movies.filter(
            title__icontains=search_query
        )

    if selected_genre:
        movies = movies.filter(
            genre__iexact=selected_genre
        )

    if selected_language:
        movies = movies.filter(
            language__iexact=selected_language
        )

    # Show only movies available on the chosen date.
    movies = movies.filter(
        Q(start_date__isnull=True)
        | Q(start_date__lte=selected_date),
        Q(end_date__isnull=True)
        | Q(end_date__gte=selected_date),
    )

    genres = (
        Movie.objects.exclude(genre="")
        .values_list("genre", flat=True)
        .distinct()
        .order_by("genre")
    )

    languages = (
        Movie.objects.exclude(language="")
        .values_list("language", flat=True)
        .distinct()
        .order_by("language")
    )

    # A showtime either belongs to the selected date
    # or repeats throughout the movie's availability period.
    showtimes = list(
        Showtime.objects.filter(
            movie__in=movies,
        )
        .filter(
            Q(date=selected_date)
            | Q(date__isnull=True)
        )
        .select_related(
            "movie",
            "screen",
            "screen__theatre",
            "screen__theatre__city",
        )
        .order_by("time")
    )

    add_starting_prices(showtimes)

    return render(
        request,
        "bookingapp/home.html",
        {
            "movies": movies,
            "genres": genres,
            "languages": languages,
            "showtimes": showtimes,
            "selected_date": selected_date,
            "date_options": get_date_options(),
            "search_query": search_query,
            "selected_genre": selected_genre,
            "selected_language": selected_language,
        },
    )


# =========================================================
# MOVIE DETAILS
# =========================================================

def movie_detail(request, movie_id):
    create_demo_data()

    movie = get_object_or_404(
        Movie,
        id=movie_id,
    )

    selected_date = get_selected_date(
        request,
        movie,
    )

    if movie_is_available(movie, selected_date):
        showtimes = list(
            Showtime.objects.filter(
                movie=movie,
            )
            .filter(
                Q(date=selected_date)
                | Q(date__isnull=True)
            )
            .select_related(
                "screen",
                "screen__theatre",
                "screen__theatre__city",
            )
            .order_by("time")
        )
    else:
        showtimes = []

    add_starting_prices(showtimes)

    reviews = movie.reviews.all().order_by(
        "-created_at"
    )

    rating_average = reviews.aggregate(
        average=Avg("rating")
    )["average"]

    return render(
        request,
        "bookingapp/movie_detail.html",
        {
            "movie": movie,
            "showtimes": showtimes,
            "reviews": reviews,
            "rating_average": rating_average,
            "selected_date": selected_date,
            "date_options": get_date_options(movie),
        },
    )


# =========================================================
# ADD MOVIE REVIEW
# =========================================================

def add_review(request, movie_id):
    movie = get_object_or_404(
        Movie,
        id=movie_id,
    )

    if request.method != "POST":
        return redirect(
            "movie_detail",
            movie_id=movie.id,
        )

    reviewer_name = request.POST.get(
        "reviewer_name",
        "",
    ).strip()

    comment = request.POST.get(
        "comment",
        "",
    ).strip()

    try:
        rating = int(
            request.POST.get("rating", "0")
        )
    except (ValueError, TypeError):
        rating = 0

    if not reviewer_name:
        messages.error(
            request,
            "Please enter your name.",
        )

    elif not comment:
        messages.error(
            request,
            "Please write a review.",
        )

    elif rating < 1 or rating > 5:
        messages.error(
            request,
            "Please select a rating between 1 and 5.",
        )

    else:
        MovieReview.objects.create(
            movie=movie,
            reviewer_name=reviewer_name,
            rating=rating,
            comment=comment,
        )

        messages.success(
            request,
            "Your review was submitted.",
        )

    return redirect(
        "movie_detail",
        movie_id=movie.id,
    )


# =========================================================
# BOOK TICKETS
# =========================================================

def book_ticket(request, showtime_id):
    showtime = get_object_or_404(
        Showtime.objects.select_related(
            "movie",
            "screen",
            "screen__theatre",
        ),
        pk=showtime_id,
    )

    movie = showtime.movie

    selected_date = requested_booking_date(
        request,
        showtime,
    )

    if selected_date is None:
        messages.error(
            request,
            "This show is not available on that date. "
            "Please choose a valid booking date.",
        )

        return redirect(
            "movie_detail",
            movie_id=movie.id,
        )

    seat_sections, all_seats, seat_prices = get_seat_sections(
        showtime
    )

    # PROCESS A BOOKING
    if request.method == "POST":
        customer_name = request.POST.get(
            "customer_name",
            "",
        ).strip()

        customer_email = request.POST.get(
            "customer_email",
            "",
        ).strip()

        selected_seats_text = request.POST.get(
            "selected_seats",
            "",
        ).strip()

        selected_seats = [
            seat.strip()
            for seat in selected_seats_text.split(",")
            if seat.strip()
        ]

        if not customer_name:
            messages.error(
                request,
                "Please enter your name.",
            )

        elif not customer_email:
            messages.error(
                request,
                "Please enter your email address.",
            )

        elif not selected_seats:
            messages.error(
                request,
                "Please select at least one seat.",
            )

        elif len(selected_seats) != len(set(selected_seats)):
            messages.error(
                request,
                "Duplicate seats are not allowed.",
            )

        elif any(
            seat not in seat_prices
            for seat in selected_seats
        ):
            messages.error(
                request,
                "Invalid seat selection. Please try again.",
            )

        else:
            booking_created = False

            with transaction.atomic():
                locked_showtime = (
                    Showtime.objects.select_for_update()
                    .get(pk=showtime.pk)
                )

                booked_seats = get_booked_seat_names(
                    locked_showtime,
                    selected_date,
                )

                if any(
                    seat in booked_seats
                    for seat in selected_seats
                ):
                    messages.error(
                        request,
                        "One or more seats are already booked "
                        "for this date and showtime. "
                        "Please select different seats.",
                    )

                else:
                    total_paid = sum(
                        (
                            seat_prices[seat]
                            for seat in selected_seats
                        ),
                        Decimal("0.00"),
                    )

                    booking = SeatBooking.objects.create(
                        showtime=locked_showtime,
                        booked_for_date=selected_date,
                        customer_name=customer_name,
                        customer_email=customer_email,
                        selected_seats=", ".join(
                            selected_seats
                        ),
                        total_paid=total_paid,
                    )

                    request.session["last_booking_id"] = booking.id
                    booking_created = True

            if booking_created:
                messages.success(
                    request,
                    "Your demo booking was created successfully.",
                )

                return redirect("booking_history")

        return redirect(
            f"{request.path}?date={selected_date.isoformat()}"
        )

    booked_seats = get_booked_seat_names(
        showtime,
        selected_date,
    )

    return render(
        request,
        "bookingapp/seats.html",
        {
            "showtime": showtime,
            "movie": movie,
            "selected_date": selected_date,
            "seat_sections": seat_sections,
            "all_seats": all_seats,
            "booked_seats": booked_seats,
            "screen_capacity": 160,
        },
    )


# =========================================================
# BOOKING HISTORY
# =========================================================

def booking_history(request):
    bookings = SeatBooking.objects.none()

    if request.method == "POST":
        email = request.POST.get(
            "customer_email",
            "",
        ).strip()

        if email:
            bookings = (
                SeatBooking.objects.filter(
                    customer_email__iexact=email
                )
                .select_related(
                    "showtime",
                    "showtime__movie",
                    "showtime__screen",
                )
                .order_by("-booked_at")
            )

        return render(
            request,
            "bookingapp/booking_history.html",
            {
                "bookings": bookings,
                "searched": True,
                "customer_email": email,
            },
        )

    last_booking_id = request.session.get(
        "last_booking_id"
    )

    if last_booking_id:
        bookings = (
            SeatBooking.objects.filter(
                id=last_booking_id
            )
            .select_related(
                "showtime",
                "showtime__movie",
                "showtime__screen",
            )
        )

        return render(
            request,
            "bookingapp/booking_history.html",
            {
                "bookings": bookings,
                "searched": False,
                "booking_confirmed": True,
            },
        )

    return render(
        request,
        "bookingapp/booking_history.html",
        {
            "bookings": bookings,
            "searched": False,
            "booking_confirmed": False,
        },
    )