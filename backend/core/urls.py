from django.urls import re_path

from .views import AboutView, HealthView, SearchView

urlpatterns = [
    re_path(r"^about/?$", AboutView.as_view(), name="about"),
    re_path(r"^search/?$", SearchView.as_view(), name="search"),
    re_path(r"^health/?$", HealthView.as_view(), name="health"),
    re_path(r"^$", HealthView.as_view()),
]
