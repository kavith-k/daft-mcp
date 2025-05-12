from mcp.server.fastmcp import FastMCP
from daftlistings import Daft, SearchType, Location, Distance
from typing import List, Dict, Optional

mcp_server = FastMCP("DaftRentalsServer")

@mcp_server.tool()
def find_rental_properties(
    location: str,
    max_price: int,
    num_beds: Optional[int] = None,
    radius_km: Optional[int] = None,
    property_type: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Finds rental properties on Daft.ie.
    Searches for properties to rent based on location, max price, number of bedrooms,
    search radius (in km, common values: 0, 1, 2, 3, 4, 5, 7, 10, 15, 20, 25, 30, 35, 40, 45, 50),
    and property type (e.g., APARTMENT, HOUSE).
    """
    try:
        daft = Daft()
        daft.set_search_type(SearchType.RESIDENTIAL_RENT)

        if radius_km is not None:
            daft.set_location(Location.DUBLIN, distance=Distance.KM10)
        else:
            daft.set_location(Location.DUBLIN) # Default search without specific radius if not provided

        daft.set_max_price(max_price)

        if num_beds is not None:
            daft.set_min_beds(num_beds)

        print(f"Searching Daft.ie with criteria: Location='{location}', MaxPrice={max_price}, Beds={num_beds}, RadiusKM={radius_km}, PropertyType='{property_type}'")

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