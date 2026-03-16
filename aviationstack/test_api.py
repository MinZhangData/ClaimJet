import requests
import json
import os
from datetime import datetime
from eu261_decision_rule import EU261DecisionRule


def get_flight_by_date_and_number(flights_data, flight_date, flight_number):
    """
    Get all flights matching specific flight_date and flight_number.
    
    Args:
        flights_data: API response containing list of flights
        flight_date: Date in format 'YYYY-MM-DD' (e.g., '2026-03-17')
        flight_number: Flight number as string (e.g., '4929' or '1605')
    
    Returns:
        List of matching flight dictionaries
    """
    matching_flights = []
    for flight in flights_data.get('data', []):
        if (flight.get('flight_date') == flight_date and 
            flight.get('flight', {}).get('number') == flight_number):
            matching_flights.append(flight)
    return matching_flights


def load_local_flight_data(filepath):
    """Load flight data from local JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def display_flight_details(flight):
    """Display formatted flight information."""
    flight_info = flight.get('flight', {})
    departure = flight.get('departure', {})
    arrival = flight.get('arrival', {})
    airline = flight.get('airline', {})
    
    print(f"\n{'='*70}")
    print(f"FLIGHT DETAILS")
    print(f"{'='*70}")
    print(f"Date: {flight.get('flight_date')}")
    print(f"IATA Code: {flight_info.get('iata', 'N/A')}")
    print(f"Flight Number: {flight_info.get('number', 'N/A')}")
    print(f"Status: {flight.get('flight_status', 'N/A')}")
    print(f"Airline: {airline.get('name', 'N/A')} ({airline.get('iata', 'N/A')})")
    print()
    print(f"DEPARTURE:")
    print(f"  Airport: {departure.get('airport', 'N/A')} ({departure.get('iata', 'N/A')})")
    print(f"  Scheduled: {departure.get('scheduled', 'N/A')}")
    print(f"  Delay: {departure.get('delay', 'N/A')} min")
    print()
    print(f"ARRIVAL:")
    print(f"  Airport: {arrival.get('airport', 'N/A')} ({arrival.get('iata', 'N/A')})")
    print(f"  Scheduled: {arrival.get('scheduled', 'N/A')}")
    print(f"  Delay: {arrival.get('delay', 'N/A')} min")
    print(f"{'='*70}")


def main():
    """Main function to search and analyze flights."""
    
    # Get user inputs
    print("\n" + "="*70)
    print("FLIGHT DELAY ANALYSIS - EU 261/2004 Compensation Checker")
    print("="*70)
    
    flight_date = input("\nEnter flight date (YYYY-MM-DD, e.g., 2026-03-17): ").strip()
    flight_number = input("Enter flight number (e.g., 4929 or 1605): ").strip()
    
    # Validate date format
    try:
        datetime.strptime(flight_date, '%Y-%m-%d')
    except ValueError:
        print(f"\n❌ Invalid date format: {flight_date}")
        print("Please use format YYYY-MM-DD")
        return
    
    # Try to load from local file first (useful for testing/demo)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_file = os.path.join(script_dir, 'api_results.json')
    
    api_response = None
    source = None
    
    # Try local file first
    if os.path.exists(local_file):
        print(f"\n📂 Found local data file. Loading from {local_file}...")
        api_response = load_local_flight_data(local_file)
        if api_response:
            source = "local file"
    
    # Fall back to API if local file not available or doesn't have data
    if not api_response or not api_response.get('data'):
        print(f"\n🌐 Fetching from Aviation Stack API...")
        
        params = {
            'access_key': 'e20e7bed45a2ceacb137580a8dae223f',
            'flight_date': flight_date,
            'flight_number': flight_number
        }
        
        try:
            api_result = requests.get('https://api.aviationstack.com/v1/flights', params)
            api_response = api_result.json()
            source = "API (date + flight number filter)"
            
            # If no results, try without filters for local filtering
            if not api_response.get('data'):
                print(f"⚠️  No results with date filter. Trying general search...")
                params = {'access_key': 'e20e7bed45a2ceacb137580a8dae223f'}
                api_result = requests.get('https://api.aviationstack.com/v1/flights', params)
                api_response = api_result.json()
                source = "API (general) - filtered locally"
        
        except requests.exceptions.RequestException as e:
            print(f"\n❌ API Error: {e}")
            return
        except json.JSONDecodeError:
            print(f"\n❌ Error parsing API response")
            return
    
    # Get matching flights
    matching_flights = get_flight_by_date_and_number(api_response, flight_date, flight_number)
    
    if not matching_flights:
        print(f"\n❌ No flights found matching your criteria.")
        print(f"   Date: {flight_date}")
        print(f"   Flight Number: {flight_number}")
        print(f"   Source: {source}")
        return
    
    print(f"\n✓ Found {len(matching_flights)} flight(s) from {source}\n")
    
    # Display and analyze each flight
    for idx, flight in enumerate(matching_flights, 1):
        display_flight_details(flight)
        
        # Run EU 261/2004 analysis
        print(f"\nEU 261/2004 ANALYSIS FOR FLIGHT {idx}:")
        engine = EU261DecisionRule(flight)
        result = engine.evaluate(
            is_extraordinary_circumstance=False,
            flight_distance_km=None
        )
        
        print(f"Status: {result.status.value.upper()}")
        print(f"Arrival Delay: {result.delay_minutes} minutes (threshold: 180 min)")
        if result.compensation_amount_eur:
            print(f"Potential Compensation: €{result.compensation_amount_eur}")
        print()
        print(f"Decision: {result.reason}")
        print()


if __name__ == "__main__":
    main()