from brecon_planner import BreconBeaconsPlanner

def test_planner():
    try:
        print("Testing BreconBeaconsPlanner...")
        planner = BreconBeaconsPlanner()
        
        print("Testing OSM data fetch...")
        planner.fetch_osm_data()
        
        print("Testing scenic locations identification...")
        locations = planner.identify_scenic_locations()
        print(f"Found {len(locations)} scenic locations")
        
        print("Testing itinerary generation...")
        itinerary = planner.generate_itinerary()
        print(f"Generated itinerary with {len(itinerary)} days")
        
        print("Testing itinerary formatting...")
        formatted = planner.format_itinerary(itinerary)
        print("Formatted itinerary:", formatted)
        
        print("All tests passed!")
        return True
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_planner() 