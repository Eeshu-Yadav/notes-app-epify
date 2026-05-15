from django.urls import path

from .views import LoginView, MeView, RegisterView

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("register/", RegisterView.as_view()),
    path("login", LoginView.as_view(), name="login"),
    path("login/", LoginView.as_view()),
    path("me", MeView.as_view(), name="me"),
    path("me/", MeView.as_view()),
]
