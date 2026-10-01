from django.urls import path

from .views import AccountLoginView, AccountLogoutView, RegisterView


urlpatterns = [
    path('login/', AccountLoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', AccountLogoutView.as_view(), name='logout'),
]