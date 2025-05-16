# trips/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_trip, name='create_trip'),
    path('results/<str:city_name>/', views.show_trip_results, name='show_trip_results'),
    # AJAX endpoint for loading more hotels - REMOVED as Amadeus returns all hotels at once
    # path('ajax/load_more_hotels/<str:city_name>/', views.load_more_hotels_ajax, name='load_more_hotels_ajax'),
]
