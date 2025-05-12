import requests
import json
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from daftlistings import Daft, SearchType, Location, Distance, PropertyType
from typing import List, Dict, Optional

load_dotenv()
mcp_server = FastMCP("DaftMCPServer")

def get_llm_response(prompt: str) -> Optional[str]:
    """Sends a prompt to the LLM and returns the text response."""
    try:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("Error: OPENROUTER_API_KEY environment variable not set.")

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-Title": "DaftMCPServer",
            },
            data=json.dumps({
                "model": "google/gemini-2.0-flash-001",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            })
        )
        response.raise_for_status()
        result = response.json()

        if result.get("choices") and len(result["choices"]) > 0:
            return result["choices"][0].get("message", {}).get("content", "").strip()
        else:
            print(f"Error: Unexpected response structure from OpenRouter API: {result}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error calling OpenRouter API: {e}")
        return None
    except Exception as e:
        print(f"Error in get_llm_response: {e}")
        return None

def map_location_to_daft_location(location: str) -> Optional[Location]:
    """Maps a user-provided location string to a daftlistings Location enum value using an LLM."""
    try:
        daft_locations_map = {loc.value["displayName"]: loc.name for loc in Location} # E.g.: {"Dublin": "DUBLIN"}

        prompt = f"""Given the user input location "{location}", which of the following valid locations is the closest match? 
Valid locations: {list(daft_locations_map.keys())}
Please return only the single best matching location name from the list provided."""

        llm_choice = get_llm_response(prompt)

        # Validate if the LLM choice is one of the valid display names
        if llm_choice in daft_locations_map:
            enum_name = daft_locations_map[llm_choice]
            return getattr(Location, enum_name)
        else:
            raise ValueError(f"Error: LLM returned an invalid location '{llm_choice}'.")

    except Exception as e:
        raise ValueError(f"Error in map_location_to_daft_location: {e}")

def map_radius_to_daft_distance(radius_km: int) -> Optional[Distance]:
    """Maps a user-provided radius in km to a daftlistings Distance enum value.
    If the radius is not an exact valid daftlistings Distance, it maps to the closest valid Distance.
    """
    # Mapping from km distance to daftlistings Distance enum
    distance_enum_map = {
        0: Distance.KM0,
        1: Distance.KM1,
        3: Distance.KM3,
        5: Distance.KM5,
        10: Distance.KM10,
        20: Distance.KM20,
    }
    
    valid_distances = list(distance_enum_map.keys()) # [0, 1, 3, 5, 10, 20]

    if radius_km in distance_enum_map:
        # Exact match found
        distance_to_map = radius_km
    else:
        # No exact match, find the closest valid distance
        closest_distance = min(valid_distances, key=lambda x: abs(x - radius_km))
        distance_to_map = closest_distance
    
    # Return the corresponding enum value using the pre-defined map
    return distance_enum_map.get(distance_to_map)

def map_property_type_to_daft_property_type(property_type: str) -> Optional[PropertyType]:
    """Maps a user-provided property type to a daftlistings PropertyType enum value using an LLM."""
    try:
        daft_property_types = [p.name for p in PropertyType] # E.g.: ["APARTMENT", "HOUSE", "DUPLEX"]

        prompt = f"""Given the user input property type "{property_type}", which of the following valid property types is the closest match? 
Valid property types: {daft_property_types}
Please return only the single best matching property type name from the list provided."""

        llm_choice = get_llm_response(prompt)

        if llm_choice in daft_property_types:
            return getattr(PropertyType, llm_choice)
        else:
            raise ValueError(f"Error: LLM returned an invalid property type '{llm_choice}'.")
    except Exception as e:
        raise ValueError(f"Error in map_property_type_to_daft_property_type: {e}")

@mcp_server.tool()
def find_rental_properties(
    location: str,
    max_price: int,
    num_beds: Optional[int],
    radius_km: Optional[int] = None,
    property_type: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Finds rental properties on Daft.ie.
    Searches for properties to rent based on location, max price, number of bedrooms,
    search radius (in km, accepted values: 0, 1, 3, 5, 10, 20),
    and property type.
    """
    try:
        daft = Daft()
        daft.set_search_type(SearchType.RESIDENTIAL_RENT)
        daft.set_max_price(max_price)
        daft.set_min_beds(num_beds)

        # Use the mapping function to get the daftlistings Location enum value
        daft_location = map_location_to_daft_location(location)
        if not daft_location:
            raise ValueError(f"Error: Could not map location '{location}'.")

        if radius_km is not None:
            daft.set_location(daft_location, distance=map_radius_to_daft_distance(radius_km))
        else:
            daft.set_location(daft_location) # Search with mapped location without specific radius

        if property_type is not None:
            daft.set_property_type(map_property_type_to_daft_property_type(property_type))

        print(f"Searching Daft.ie with criteria: Location='{daft_location.name}', MaxPrice={max_price}, Beds={num_beds}, RadiusKM={radius_km}, PropertyType='{property_type}'")

        listings = daft.search(max_pages=1)

        results = []
        if listings:
            for listing in listings:
                # Ensure price is available and format it
                price_str = "Price not listed"
                if listing.price:
                    price_str = listing.price
                    # Basic cleaning if price comes with "From", "per month" etc.
                    # This might need more robust parsing based on actual `daftlistings` output
                    if isinstance(price_str, str):
                        price_str = price_str.replace("\u20ac", "€").split(" ")[0]


                listing_details = {
                    "title": listing.title if listing.title else "N/A",
                    "price": price_str,
                    "link": listing.daft_link if listing.daft_link else "N/A",
                }
                results.append(listing_details)
        
        if not results:
            return [{"message": "No properties found matching your criteria."}]

        return results

    except Exception as e:
        print(f"Error in find_rental_properties: {e}")
        return [{"error": f"An error occurred: {str(e)}"}]

if __name__ == "__main__":
    print(f"Starting server {mcp_server.name}...")
    mcp_server.run(transport="stdio") 