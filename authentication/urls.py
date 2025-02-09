from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from .views import homepage, register, LoginView

app_name = "authentication"

urlpatterns = [
    path('', homepage, name="homepage"),
    path('register/', register, name="register"),
    path('login/', LoginView.as_view(), name="login"),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('profile/', views.profile, name="profile"),
    path('my-upload/', views.my_upload, name="my_upload"),
    path('forbidden/', views.forbidden, name="forbidden"),
]
