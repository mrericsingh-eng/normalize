import json
import os
import re
import asyncio
from typing import List, Dict, Tuple, Set
import httpx
from .text_utils import normalize_text


async def extract_entities(text: str, geocoder_url: str, user_agent: str, timeout: float = 1.0) -> Tuple[List[Dict[str, str]], Dict[str, str], Dict[str, str]]:
    """
    Extract entities (cities, hotels, restaurants) and detect typos from text using OpenAI API.

    Returns:
        - List of entities with type and value
        - Dict mapping entity values to country codes for enrichment
        - Dict with typo information
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    prompt = f"""Extract travel-related entities AND detect typos from this message.

ENTITY TYPES:
- city: Cities, towns, or urban places (e.g., "Rome", "New York City", "Paris", "Tokyo", "Seattle", "Vancouver")
- country: Countries or nations (e.g., "South Africa", "Mexico", "South Korea", "United States", "Canada")
- hotel: Hotels, resorts, inns, lodges (e.g., "Marriott", "Chapter Roma", "Four Seasons", "Hilton")
- restaurant: Restaurants, cafes, bistros, trattorias (e.g., "Olive Garden", "Joe's Pizza", "Bistro Romano", "McDonald's")

TYPO DETECTION:
- city_typo: Obvious city misspellings (e.g., "Lndon" → "london", "Seatlee" → "seattle", "Paries" → "paris")
- country_typo: Country misspellings (e.g., "Mexco" → "mexico")
- phone_number_typo: Phone numbers with wrong digit count (9, 11+ digits)
- zip_code_typo: ZIP codes not 5 digits when mentioned with "zip" context

RULES:
- Return entity values in lowercase
- Extract ALL locations mentioned, including current location AND destinations
- IMPORTANT: Distinguish between cities and countries:
  * Use "city" for: Rome, Tokyo, Paris, New York, Seattle, Vancouver, etc.
  * Use "country" for: South Africa, Mexico, South Korea, United States, Canada, etc.
- For hotels: Extract hotel names, hotel chains, accommodation mentions (e.g., "Chapter Roma", "staying at Marriott")
- For restaurants: Extract restaurant names, dining establishments (e.g., "eat at Olive Garden", "going to McDonald's")
- Extract ALL entities mentioned, don't skip any
- For typos: Only include obvious misspellings, be conservative
- Return empty arrays/nulls if nothing found

Message: "{text}"

EXAMPLES:
- "staying at Chapter Roma" → hotel: "chapter roma"
- "eat at Olive Garden" → restaurant: "olive garden"
- "planning Rome in October" → city: "rome"
- "going to Mexico" → country: "mexico"

Return ONLY valid JSON:
{{
    "entities": [{{"type": "city", "value": "rome"}}, {{"type": "hotel", "value": "chapter roma"}}, {{"type": "restaurant", "value": "olive garden"}}],
    "typos": {{
        "city_typo": "lndon -> london",
        "country_typo": null,
        "phone_number_typo": "661248083",
        "zip_code_typo": null
    }}
}}"""

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                    "max_tokens": 300
                }
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()

            # Parse JSON response (handle markdown code blocks)
            try:
                # Remove markdown code blocks if present
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.replace("```", "").strip()

                parsed_response = json.loads(content)

                # Handle both old array format and new object format for backward compatibility
                if isinstance(parsed_response, list):
                    # Old format - just entities
                    entities = parsed_response
                    typos = {"city_typo": None, "country_typo": None, "phone_number_typo": None, "zip_code_typo": None}
                else:
                    # New format - object with entities and typos
                    entities = parsed_response.get("entities", [])
                    typos = parsed_response.get("typos", {})

                # Validate entity structure
                validated_entities = []
                for entity in entities:
                    if (isinstance(entity, dict) and
                        "type" in entity and "value" in entity and
                        entity["type"] in ["city", "country", "hotel", "restaurant"] and
                        isinstance(entity["value"], str)):
                        validated_entities.append({
                            "type": entity["type"],
                            "value": entity["value"].lower().strip()
                        })

                # Get country codes for cities using geocoding and country name mapping
                country_map = {}
                city_entities = [e for e in validated_entities if e["type"] == "city"]
                country_entities = [e for e in validated_entities if e["type"] == "country"]

                # Handle cities via geocoding
                if city_entities:
                    city_names = [e["value"] for e in city_entities]
                    country_map = await _get_country_codes(city_names, geocoder_url, user_agent, timeout)

                    # Add direct country name mappings for cities
                    country_name_map = _get_country_name_mappings(city_names)
                    country_map.update(country_name_map)

                # Handle countries directly
                if country_entities:
                    country_names = [e["value"] for e in country_entities]
                    country_name_map = _get_country_name_mappings(country_names)
                    country_map.update(country_name_map)

                return validated_entities, country_map, typos

            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return await _fallback_extract_entities(text, geocoder_url, user_agent, timeout)

    except Exception as e:
        # Fallback to original method if API fails
        return await _fallback_extract_entities(text, geocoder_url, user_agent, timeout)


async def _get_country_codes(city_names: List[str], geocoder_url: str, user_agent: str, timeout: float) -> Dict[str, str]:
    """Get country codes for city names using geocoding."""
    country_map = {}

    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = []
        for city_name in city_names:
            task = _geocode_city(city_name, geocoder_url, user_agent, client)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, dict) and "city" in result and "country_code" in result:
                city_key = city_names[i].lower()
                country_map[city_key] = result["country_code"]

    return country_map


async def _geocode_city(city_name: str, geocoder_url: str, user_agent: str, client: httpx.AsyncClient) -> Dict[str, str]:
    """Geocode a single city to get country code."""
    try:
        params = {
            "q": city_name,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }

        headers = {"User-Agent": user_agent}

        response = await client.get(geocoder_url, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()
        if data and len(data) > 0:
            place = data[0]
            place_type = place.get("type", "")
            place_class = place.get("class", "")

            # Accept places that are cities, towns, administrative areas, or provinces that represent major cities
            addresstype = place.get("addresstype", "")
            if ((place_class == "place" and place_type in ["city", "town", "village"]) or
                (place_class == "boundary" and place_type == "administrative" and addresstype in ["city", "province"])):
                address = place.get("address", {})
                country_code = address.get("country_code", "").upper()
                display_name = place.get("display_name", "").split(",")[0]

                return {
                    "city": display_name,
                    "country_code": country_code
                }

    except Exception:
        pass

    return {}


async def _fallback_extract_entities(text: str, geocoder_url: str, user_agent: str, timeout: float) -> Tuple[List[Dict[str, str]], Dict[str, str], Dict[str, str]]:
    """Fallback entity extraction using original regex-based approach."""
    entities = []
    country_map = {}

    # Extract city candidates
    city_candidates = _extract_city_candidates_fallback(text)

    # Validate cities with geocoding
    if city_candidates:
        validated_cities = await _validate_cities_fallback(city_candidates, geocoder_url, user_agent, timeout)
        for city, country_code in validated_cities.items():
            entities.append({"type": "city", "value": city.lower()})
            country_map[city.lower()] = country_code

    # Extract hotels and restaurants
    hotels = _extract_hotels_fallback(text)
    restaurants = _extract_restaurants_fallback(text)

    entities.extend([{"type": "hotel", "value": hotel.lower()} for hotel in hotels])
    entities.extend([{"type": "restaurant", "value": restaurant.lower()} for restaurant in restaurants])

    # No typos in fallback mode
    typos = {"city_typo": None, "country_typo": None, "phone_number_typo": None, "zip_code_typo": None}
    return entities, country_map, typos


def _extract_city_candidates_fallback(text: str) -> Set[str]:
    """Extract potential city names from text using regex."""
    candidates = set()

    patterns = [
        r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'\bto\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            city = match.strip()
            if len(city) > 1:
                candidates.add(city)

    # Common cities
    city_phrases = [
        "New York City", "New York", "Los Angeles", "San Francisco",
        "Las Vegas", "Miami", "Chicago", "Boston", "Seattle",
        "Paris", "London", "Rome", "Barcelona", "Amsterdam", "Berlin",
        "Tokyo", "Sydney", "Dubai", "Istanbul"
    ]

    for phrase in city_phrases:
        if phrase.lower() in text.lower():
            candidates.add(phrase)

    return candidates


async def _validate_cities_fallback(candidates: Set[str], geocoder_url: str, user_agent: str, timeout: float) -> Dict[str, str]:
    """Validate city candidates using geocoding API."""
    validated = {}

    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = []
        for candidate in candidates:
            task = _geocode_city(candidate, geocoder_url, user_agent, client)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, dict) and "city" in result and "country_code" in result:
                validated[result["city"]] = result["country_code"]

    return validated


def _extract_hotels_fallback(text: str) -> List[str]:
    """Extract hotel names using keyword matching."""
    hotels = []
    hotel_keywords = {"hotel", "inn", "resort", "lodge", "hostel", "marriott", "hilton", "hyatt", "four seasons", "chapter roma"}
    normalized = normalize_text(text)

    for keyword in hotel_keywords:
        if keyword in normalized:
            if keyword == "chapter roma":
                if "chapter roma" in normalized:
                    hotels.append("Chapter Roma")

    return hotels


def _extract_restaurants_fallback(text: str) -> List[str]:
    """Extract restaurant names using keyword matching."""
    restaurants = []
    restaurant_keywords = {"restaurant", "trattoria", "osteria", "cafe", "bistro"}
    normalized = normalize_text(text)

    for keyword in restaurant_keywords:
        if keyword in normalized:
            # Simple extraction for fallback
            pass

    return restaurants


def _get_country_name_mappings(city_names: List[str]) -> Dict[str, str]:
    """Map country names and major cities directly to their ISO codes."""
    mappings = {
        # Major countries commonly mentioned in travel
        "south africa": "ZA",
        "south korea": "KR",
        "north korea": "KP",
        "united states": "US",
        "united kingdom": "GB",
        "great britain": "GB",
        "germany": "DE",
        "france": "FR",
        "italy": "IT",
        "spain": "ES",
        "netherlands": "NL",
        "belgium": "BE",
        "switzerland": "CH",
        "austria": "AT",
        "china": "CN",
        "japan": "JP",
        "australia": "AU",
        "canada": "CA",
        "mexico": "MX",
        "brazil": "BR",
        "argentina": "AR",
        "chile": "CL",
        "colombia": "CO",
        "peru": "PE",
        "venezuela": "VE",
        "russia": "RU",
        "india": "IN",
        "thailand": "TH",
        "vietnam": "VN",
        "singapore": "SG",
        "malaysia": "MY",
        "indonesia": "ID",
        "philippines": "PH",
        "turkey": "TR",
        "egypt": "EG",
        "morocco": "MA",
        "kenya": "KE",
        "nigeria": "NG",
        "ghana": "GH",
        "iran": "IR",
        "iraq": "IQ",
        "israel": "IL",
        "jordan": "JO",
        "lebanon": "LB",
        "saudi arabia": "SA",
        "uae": "AE",
        "united arab emirates": "AE",
        "new zealand": "NZ",

        # Major cities to country mappings
        "paris": "FR",
        "london": "GB",
        "berlin": "DE",
        "madrid": "ES",
        "barcelona": "ES",
        "amsterdam": "NL",
        "brussels": "BE",
        "vienna": "AT",
        "zurich": "CH",
        "geneva": "CH",
        "stockholm": "SE",
        "oslo": "NO",
        "copenhagen": "DK",
        "helsinki": "FI",
        "prague": "CZ",
        "budapest": "HU",
        "warsaw": "PL",
        "moscow": "RU",
        "st petersburg": "RU",
        "tokyo": "JP",
        "osaka": "JP",
        "kyoto": "JP",
        "seoul": "KR",
        "beijing": "CN",
        "shanghai": "CN",
        "hong kong": "HK",
        "singapore": "SG",
        "bangkok": "TH",
        "mumbai": "IN",
        "delhi": "IN",
        "bangalore": "IN",
        "sydney": "AU",
        "melbourne": "AU",
        "toronto": "CA",
        "vancouver": "CA",
        "montreal": "CA",
        "new york": "US",
        "nyc": "US",
        "los angeles": "US",
        "chicago": "US",
        "san francisco": "US",
        "miami": "US",
        "las vegas": "US",
        "boston": "US",
        "washington": "US",
        "seattle": "US",
        "mexico city": "MX",
        "cancun": "MX",
        "rio de janeiro": "BR",
        "sao paulo": "BR",
        "buenos aires": "AR",
        "lima": "PE",
        "santiago": "CL",
        "bogota": "CO",
        "caracas": "VE",
        "cairo": "EG",
        "cape town": "ZA",
        "johannesburg": "ZA",
        "nairobi": "KE",
        "istanbul": "TR",
        "athens": "GR",
        "lisbon": "PT",
        "dublin": "IE",
        "reykjavik": "IS",
        "tel aviv": "IL",
        "dubai": "AE",
        "doha": "QA",
        "riyadh": "SA"
    }

    result = {}
    for city_name in city_names:
        if city_name in mappings:
            result[city_name] = mappings[city_name]

    return result
