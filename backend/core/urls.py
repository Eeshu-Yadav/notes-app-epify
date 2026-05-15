from django.urls import path

from .views import AboutView, HealthView, SearchView

urlpatterns = [
    path("about", AboutView.as_view(), name="about"),
    path("about/", AboutView.as_view()),
    path("search", SearchView.as_view(), name="search"),
    path("search/", SearchView.as_view()),
    path("health", HealthView.as_view(), name="health"),
    path("", HealthView.as_view()),  # root → 200 ok (avoids confusing 404 in browsers)
]
