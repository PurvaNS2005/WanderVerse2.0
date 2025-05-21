from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse
from .forms import TripForm
from .utils.geodb_api import get_city_coordinates
from .utils.geoapify_api import get_pois
from .utils.hotel_api import get_amadeus_token, get_city_code, get_hotels_in_city 
from .utils.gemini_api import generate_itinerary
from datetime import datetime
import json

# HOTELS_PER_PAGE constant is no longer needed for Amadeus hotel fetching

def create_trip(request):
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            city = form.cleaned_data['city']
            request.session['start_date'] = form.cleaned_data['start_date'].strftime('%Y-%m-%d')
            request.session['end_date'] = form.cleaned_data['end_date'].strftime('%Y-%m-%d')
            return redirect(reverse('show_trip_results', kwargs={'city_name': city}))
    else:
        form = TripForm()
    return render(request, 'trips/initiate_trip.html', {'form': form})


def show_trip_results(request, city_name):
    city_info = get_city_coordinates(city_name)
    context = {'city_name_searched': city_name}
    
    check_in_date_str = request.session.get('start_date') 
    check_out_date_str = request.session.get('end_date')

    if not city_info:
        messages.error(request, f"Sorry, city '{city_name}' could not be found.")
        return redirect(reverse('create_trip'))

    lat, lon = city_info['lat'], city_info['lon']
    
    # Fetch POIs with multiple categories
    pois = []
    categories = [
        'tourism.sights',  # Tourist attractions
        'tourism.museum',  # Museums
        'tourism.attraction',  # General attractions
        'tourism.historic',  # Historic sites
        'tourism.art',  # Art galleries
        'tourism.park',  # Parks
        'tourism.viewpoint',  # Viewpoints
        'tourism.architecture',  # Architectural landmarks
        'tourism.monument',  # Monuments
        'tourism.cultural',  # Cultural sites
    ]
    
    for category in categories:
        category_pois = get_pois(lat, lon, category=[category])
        pois.extend(category_pois)
    
    # Remove duplicates based on name
    seen_names = set()
    unique_pois = []
    for poi in pois:
        name = poi.get('properties', {}).get('name')
        if name and name not in seen_names:
            seen_names.add(name)
            unique_pois.append(poi)
    
    pois = unique_pois[:20]  # Limit to 20 unique POIs
    
    token = get_amadeus_token()

    hotels_list = []

    if not token:
        messages.warning(request, "Failed to authenticate for hotel search. Hotel list may be unavailable.")
    else:
        city_code = get_city_code(city_name, token)
        if not city_code:
            messages.warning(request, f"Could not find IATA code for '{city_name}'. Hotel list may be unavailable.")
        else:
            print(f"Fetching hotel details for city code: {city_code}")
            hotel_data_response = get_hotels_in_city(city_code, token) # Fetches all hotels
            hotels_list = hotel_data_response.get("hotels", [])
            # meta = hotel_data_response.get("meta") # Meta not used for pagination now

            if not hotels_list:
                messages.info(request, f"No hotels found for '{city_name}' via Amadeus.")
            else:
                print(f"--- Hotels Data from get_hotels_in_city in View ({city_name}) - Count: {len(hotels_list)} ---")
                # No longer need to print all hotels here, it can be too much
                # for i, hotel_data in enumerate(hotels_list):
                #     print(f"Hotel {i+1}:")
                #     print(json.dumps(hotel_data, indent=2))
                # print(f"--- End of Hotels Data from get_hotels_in_city in View ---")

    context.update({
        'city_info': city_info, 
        'pois': pois,
        'hotels': hotels_list, # Pass all hotels to the template
        'check_in_date': check_in_date_str,
        'check_out_date': check_out_date_str 
    })
    return render(request, 'trips/trip_results.html', context)

# load_more_hotels_ajax view is removed as it's no longer needed for Amadeus hotels

def ai_itinerary_form(request, city_name):
    """Display the AI itinerary generation form"""
    return render(request, 'trips/ai_itinerary.html', {
        'city_name': city_name
    })

def generate_ai_itinerary(request, city_name):
    """Handle the AI itinerary generation form submission"""
    if request.method == 'POST':
        try:
            # Get form data
            prompt = request.POST.get('prompt')
            travel_style = request.POST.get('travel_style', 'balanced')
            budget = request.POST.get('budget', 'medium')
            
            if not prompt:
                messages.error(request, 'Please provide a prompt for the itinerary generation.')
                return redirect('ai_itinerary_form', city_name=city_name)
            
            # Get dates from session
            check_in_date_str = request.session.get('start_date')
            check_out_date_str = request.session.get('end_date')
            
            if not check_in_date_str or not check_out_date_str:
                messages.error(request, 'Missing date information. Please start over.')
                return redirect('create_trip')
            
            # Generate itinerary with custom prompt
            itinerary = generate_itinerary(
                city_name=city_name,
                start_date=check_in_date_str,
                end_date=check_out_date_str,
                preferences={
                    "prompt": prompt,
                    "travel_style": travel_style,
                    "budget": budget
                }
            )
            
            # Store the itinerary in session for display
            request.session['ai_itinerary'] = itinerary
            
            # Redirect to display the generated itinerary
            return redirect('show_ai_itinerary', city_name=city_name)
            
        except Exception as e:
            messages.error(request, f'Error generating itinerary: {str(e)}')
            return redirect('ai_itinerary_form', city_name=city_name)
    
    return redirect('ai_itinerary_form', city_name=city_name)

def show_ai_itinerary(request, city_name):
    """Display the generated AI itinerary"""
    itinerary = request.session.get('ai_itinerary')
    
    if not itinerary:
        messages.error(request, 'No itinerary found. Please generate one first.')
        return redirect('ai_itinerary_form', city_name=city_name)
    
    return render(request, 'trips/show_ai_itinerary.html', {
        'city_name': city_name,
        'itinerary': itinerary
    })

def create_itinerary(request, city_name):
    """View for creating a manual itinerary"""
    # Get city info
    city_info = get_city_coordinates(city_name)
    if not city_info:
        messages.error(request, f"Sorry, city '{city_name}' could not be found.")
        return redirect(reverse('create_trip'))
    
    # Get dates from session
    check_in_date_str = request.session.get('start_date')
    check_out_date_str = request.session.get('end_date')
    
    if not check_in_date_str or not check_out_date_str:
        messages.error(request, 'Missing date information. Please start over.')
        return redirect('create_trip')
    
    # Get POIs and hotels for the city
    lat, lon = city_info['lat'], city_info['lon']
    
    # Fetch POIs
    pois = []
    categories = [
        'tourism.sights',
        'tourism.museum',
        'tourism.attraction',
        'tourism.historic',
        'tourism.art',
        'tourism.park',
        'tourism.viewpoint',
        'tourism.architecture',
        'tourism.monument',
        'tourism.cultural',
    ]
    
    for category in categories:
        category_pois = get_pois(lat, lon, category=[category])
        pois.extend(category_pois)
    
    # Remove duplicates
    seen_names = set()
    unique_pois = []
    for poi in pois:
        name = poi.get('properties', {}).get('name')
        if name and name not in seen_names:
            seen_names.add(name)
            unique_pois.append(poi)
    
    pois = unique_pois[:20]  # Limit to 20 unique POIs
    
    # Fetch hotels
    hotels_list = []
    token = get_amadeus_token()
    if token:
        city_code = get_city_code(city_name, token)
        if city_code:
            hotel_data_response = get_hotels_in_city(city_code, token)
            hotels_list = hotel_data_response.get("hotels", [])
    
    context = {
        'city_name': city_name,
        'city_info': city_info,
        'pois': pois,
        'hotels': hotels_list,
        'check_in_date': check_in_date_str,
        'check_out_date': check_out_date_str
    }
    
    return render(request, 'trips/create_itinerary.html', context)