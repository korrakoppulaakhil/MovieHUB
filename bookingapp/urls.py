from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("movie/<int:movie_id>/", views.movie_detail, name="movie_detail"),
    path("movie/<int:movie_id>/review/", views.add_review, name="add_review"),
    path("book/<int:showtime_id>/", views.book_ticket, name="book_ticket"),
    path("my-bookings/", views.booking_history, name="booking_history"),
]