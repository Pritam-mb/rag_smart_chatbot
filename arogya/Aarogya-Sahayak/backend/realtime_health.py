import requests
import logging
from typing import List, Dict, Any
import os
import feedparser 
# Path and dotenv imports are removed as main.py handles loading

# Configure logging for the module
logging.basicConfig(level=logging.INFO)

IDSP_URL = "https://idsp.nic.in/index4.php?lang=1&level=0&linkid=406&lid=3689"

# -----------------------------------------
# WHO Outbreaks (Live RSS feed)
# -----------------------------------------
def get_who_outbreaks() -> List[Dict[str, Any]]:
    """
    Fetches recent global disease outbreaks by parsing the WHO RSS feed.
    """
    try:
        feed_url = "https://www.who.int/feeds/entity/csr/don/en/rss.xml"
        data = feedparser.parse(feed_url)

        outbreaks = []
        for entry in data.entries[:5]:
            # Extracts country based on common WHO title format (e.g., "Disease - Country")
            country_part = entry.title.split("–")[-1].strip()
            outbreaks.append({
                "title": entry.title,
                "country": country_part if len(country_part) < 50 else "Unknown Region"
            })
        return outbreaks

    except Exception as e:
        logging.error(f"Failed to fetch WHO outbreaks via RSS: {e}")
        return []

# -----------------------------------------
# India IDSP Outbreaks (Live HTTP Request)
# -----------------------------------------
def get_idsp_outbreaks() -> List[str]:
    """
    Fetches specific Indian health alerts from the IDSP website.
    NOTE: Uses robust error handling to manage unstable network connections.
    """
    try:
        r = requests.get(IDSP_URL, timeout=10)
        r.raise_for_status() # Raise exception for 4xx or 5xx status codes
        text = r.text

        headlines = []
        # Simple string parsing 
        for line in text.split("\n"):
            if "Outbreak" in line and len(headlines) < 5:
                headlines.append(line.strip()) 

        return headlines if headlines else ["IDSP alerts currently unavailable."]

    except requests.exceptions.RequestException as e:
        logging.warning(f"IDSP Network/Request Error: {e}. Returning placeholder data.")
        # Fallback placeholder data if the network call fails
        return [
            "IDSP network failed (DNS/Connection). Using default alert: Increased heat stroke cases in Delhi",
        ]
    except Exception as e:
        logging.error(f"IDSP Parsing/Unknown Error: {e}")
        return []


# -----------------------------------------
# Weather API for location-based risk
# -----------------------------------------
def get_weather(lat: float, lon: float, api_key: str) -> Dict[str, Any]: 
    """
    Fetches real-time weather data from OpenWeatherMap using a provided API key.
    """
    if not api_key: # ⬅️ CHECK THE PASSED KEY
        logging.error("WEATHER_API_KEY is missing (Passed key is empty). Cannot fetch weather.")
        return {}
        
    try:
        # ⬅️ USE THE PASSED 'api_key'
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric" 
        res = requests.get(url, timeout=10).json()
        return res
        
    except requests.exceptions.RequestException as e:
        logging.warning(f"OpenWeatherMap network error: {e}. Returning simulation data.")
        # Return a simulated structure
        return {
            "main": {"temp": 30, "humidity": 75},
            "name": "Simulated Location"
        }
    except Exception as e:
        logging.error(f"Weather API general error: {e}")
        return {}


# -----------------------------------------
# Risk Calculation
# -----------------------------------------
def calculate_disease_risk(weather: Dict[str, Any]) -> List[str]:
    """
    Calculates disease risks based on local weather conditions.
    """
    risks = []
    
    # Defensive extraction using .get() to avoid KeyError
    main_data = weather.get("main")
    
    if not main_data:
        return ["Warning: Weather data insufficient for localized risk assessment."]

    # Extract required values, assuming they exist within 'main'
    temp = main_data.get("temp")
    humidity = main_data.get("humidity")
    
    if temp is None or humidity is None:
        return ["Warning: Temperature or humidity data missing for localized risk assessment."]

    # Logic based on user's requirements
    if humidity > 80:
        risks.append("High chance of mosquito-borne diseases (Dengue/Chikungunya).")
    if temp > 35:
        risks.append("Risk of dehydration and heatstroke.")
    if temp < 15:
        risks.append("Higher chance of viral infections.")

    return risks if risks else ["Low local weather-related health risk."]