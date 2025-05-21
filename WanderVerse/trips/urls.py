# trips/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_trip, name='create_trip'),
    path('results/<str:city_name>/', views.show_trip_results, name='show_trip_results'),
    path('create-itinerary/<str:city_name>/', views.create_itinerary, name='create_itinerary'),
    path('ai-itinerary/<str:city_name>/', views.ai_itinerary_form, name='ai_itinerary_form'),
    path('generate-ai-itinerary/<str:city_name>/', views.generate_ai_itinerary, name='generate_ai_itinerary'),
    path('show-ai-itinerary/<str:city_name>/', views.show_ai_itinerary, name='show_ai_itinerary'),
    # AJAX endpoint for loading more hotels - REMOVED as Amadeus returns all hotels at once
    # path('ajax/load_more_hotels/<str:city_name>/', views.load_more_hotels_ajax, name='load_more_hotels_ajax'),
]
