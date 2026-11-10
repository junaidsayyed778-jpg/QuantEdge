from django.urls import path
from .views import RegisterView, LoginView, MeView, CSRFTokenView, LogoutView, RefreshView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("me/", MeView.as_view(), name="me"),
    path("csrf/", CSRFTokenView.as_view(), name="csrf"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", RefreshView.as_view(), name="refresh"),

]

