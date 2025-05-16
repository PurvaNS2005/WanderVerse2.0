from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('verify-token/', views.verify_token, name='verify_token'),
    path('sign-out/', views.sign_out, name='sign_out'),
    path('get-csrf-token/', views.get_csrf_token, name='get_csrf_token'),
    path('profile/', views.profile, name='profile'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('update-profile-picture/', views.update_profile_picture, name='update_profile_picture'),
] 