import asyncio
from typing import List, Dict, Optional
import httpx


async def enrich(entities: List[Dict[str, str]], country_map: Dict[str, str], 
                emergency_api_base: str, user_agent: str, timeout: float = 1.0) -> Dict[str, Optional[List[str]]]:
    """
    Enrich entities with additional information.

    Returns dict with enrichment data:
    - local_emergency_numbers: List of emergency numbers for cities
    """
    enrichment = {
        "local_emergency_numbers": None
    }

    # Get all locations from entities (cities and countries)
    locations = [entity["value"] for entity in entities if entity["type"] in ["city", "country"]]

    if not locations:
        return enrichment

    # Get emergency numbers for all locations
    emergency_numbers = await _get_emergency_numbers(locations, country_map, emergency_api_base, user_agent, timeout)
    if emergency_numbers:
        enrichment["local_emergency_numbers"] = emergency_numbers

    return enrichment


async def _get_emergency_numbers(cities: List[str], country_map: Dict[str, str], 
                                emergency_api_base: str, user_agent: str, timeout: float) -> Optional[List[str]]:
    """Get emergency numbers for cities based on their countries."""
    emergency_numbers = set()
    
    # Get unique country codes
    country_codes = set(country_map.values())
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = []
        for country_code in country_codes:
            task = _fetch_emergency_numbers(country_code, emergency_api_base, user_agent, client)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                emergency_numbers.update(result)
    
    return list(emergency_numbers) if emergency_numbers else None


async def _fetch_emergency_numbers(country_code: str, emergency_api_base: str,
                                  user_agent: str, client: httpx.AsyncClient) -> List[str]:
    """Fetch emergency numbers for a specific country."""
    try:
        url = f"{emergency_api_base}/country/{country_code}"
        headers = {"User-Agent": user_agent}

        response = await client.get(url, headers=headers)
        response.raise_for_status()

        api_response = response.json()
        numbers = []

        if isinstance(api_response, dict) and "data" in api_response:
            data = api_response["data"]

            # Check if country is member of 112 group - if so, 112 takes precedence
            is_112_member = data.get("member_112", False)
            if is_112_member:
                numbers.append("112")

            # Try to get dispatch number first (if not empty)
            dispatch = data.get("dispatch", {})
            if isinstance(dispatch, dict) and dispatch.get("all"):
                dispatch_nums = [num for num in dispatch["all"] if num.strip()]
                numbers.extend(dispatch_nums)

            # Then police number (if different and not empty)
            police = data.get("police", {})
            if isinstance(police, dict) and police.get("all"):
                police_nums = [num for num in police["all"] if num.strip() and num not in numbers]
                numbers.extend(police_nums)

        # Remove duplicates while preserving order
        seen = set()
        unique_numbers = []
        for num in numbers:
            if num not in seen:
                seen.add(num)
                unique_numbers.append(num)

        return unique_numbers

    except Exception as e:
        # Return empty list on any error
        print(f"Error fetching emergency numbers for {country_code}: {e}")
        return []


