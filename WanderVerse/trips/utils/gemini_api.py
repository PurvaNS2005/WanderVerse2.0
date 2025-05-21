import os
import json
import google.generativeai as genai
from datetime import datetime

# Configure the Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

# Configure the API with the correct version
genai.configure(api_key=GOOGLE_API_KEY)

def generate_itinerary(city_name, start_date, end_date, preferences=None):
    """
    Generate an AI-powered itinerary using Google's Gemini API.
    
    Args:
        city_name (str): Name of the city
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        preferences (dict, optional): User preferences including:
            - prompt (str): User's custom prompt
            - travel_style (str): 'relaxed', 'balanced', or 'intensive'
            - budget (str): 'budget', 'medium', or 'luxury'
    
    Returns:
        dict: Generated itinerary with daily activities
    """
    try:
        # Initialize the model with safety settings
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
        }
        
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
        ]
        
        model = genai.GenerativeModel(
            model_name="models/gemini-1.5-flash",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Format dates
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        num_days = (end - start).days + 1
        
        # Create the prompt
        prompt = f"""Create a detailed {num_days}-day travel itinerary for {city_name} from {start_date} to {end_date}.
        
        Please include:
        1. Daily activities with suggested times
        2. Popular attractions and landmarks
        3. Local restaurants and food recommendations
        4. Transportation tips between locations
        5. Estimated costs for major activities
        
        Format the response as a structured JSON with the following format:
        {{
            "itinerary": [
                {{
                    "day": 1,
                    "date": "YYYY-MM-DD",
                    "activities": [
                        {{
                            "time": "HH:MM",
                            "title": "Activity name",
                            "description": "Brief description",
                            "location": "Location name",
                            "estimated_cost": "Cost in local currency",
                            "duration": "Estimated duration"
                        }}
                    ]
                }}
            ],
            "total_estimated_cost": "Total cost in local currency",
            "additional_tips": ["Tip 1", "Tip 2", ...]
        }}
        
        Make the itinerary realistic and consider:
        - Opening hours of attractions
        - Travel time between locations
        - Local customs and best times to visit places
        - A mix of popular and off-the-beaten-path experiences
        
        IMPORTANT: Respond ONLY with valid JSON. Do not include any other text or explanation.
        """
        
        if preferences:
            # Add user preferences to the prompt
            prompt += f"\n\nConsider these preferences:\n"
            if 'prompt' in preferences:
                prompt += f"- Custom requirements: {preferences['prompt']}\n"
            if 'travel_style' in preferences:
                prompt += f"- Travel style: {preferences['travel_style']}\n"
            if 'budget' in preferences:
                prompt += f"- Budget level: {preferences['budget']}\n"
        
        # Generate the response
        response = model.generate_content(prompt)
        
        # Parse the response
        try:
            # Clean the response text to ensure it's valid JSON
            response_text = response.text.strip()
            # Remove any markdown code block markers if present
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Parse the JSON response
            itinerary_data = json.loads(response_text)
            return itinerary_data
        except json.JSONDecodeError as e:
            print(f"Error parsing Gemini response: {e}")
            print(f"Raw response: {response.text}")
            return {
                "error": "Failed to parse itinerary",
                "raw_response": response.text
            }
            
    except Exception as e:
        print(f"Error generating itinerary: {e}")
        return {
            "error": "Failed to generate itinerary",
            "details": str(e)
        } 