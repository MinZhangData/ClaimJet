"""
Aviation Stack API Timetable Data Fetcher

Fetches flight timetable data from Aviation Stack /timetable endpoint and saves to api_results.json
This ensures api_results.json contains real data for testing and offline use.
"""

import requests
import json
import os


def fetch_and_save_timetable_data(timetable_type='arrival', iata_code=None, icao_code=None):
    """
    Fetch flight timetable data from Aviation Stack API and save to api_results.json.
    
    Args:
        timetable_type: 'arrival' or 'departure' (default: 'arrival')
        iata_code: Optional IATA airport code filter (e.g., 'JFK')
        icao_code: Optional ICAO airport code filter (e.g., 'KJFK')
    """
    
    api_key = 'e20e7bed45a2ceacb137580a8dae223f'
    
    # Build parameters
    params = {
        'access_key': api_key,
        'type': timetable_type
    }
    
    if iata_code:
        params['iataCode'] = iata_code
    if icao_code:
        params['icaoCode'] = icao_code
    
    print("="*70)
    print("AVIATION STACK TIMETABLE API DATA FETCHER")
    print("="*70)
    print(f"\n🌐 Fetching {timetable_type} timetable data from Aviation Stack API...")
    if iata_code:
        print(f"   IATA Code: {iata_code}")
    if icao_code:
        print(f"   ICAO Code: {icao_code}")
    print()
    
    try:
        response = requests.get('https://api.aviationstack.com/v1/timetable', params)
        response.raise_for_status()
        
        api_data = response.json()
        
        # Check for API errors
        if api_data.get('error'):
            print(f"❌ API Error: {api_data['error'].get('info', 'Unknown error')}")
            return False
        
        # Get data count
        data_count = len(api_data.get('data', []))
        pagination = api_data.get('pagination', {})
        
        print(f"✓ Successfully fetched {data_count} flight(s)")
        if pagination:
            print(f"  Pagination Info:")
            print(f"    - Limit: {pagination.get('limit')}")
            print(f"    - Total Available: {pagination.get('total')}")
            print(f"    - Offset: {pagination.get('offset')}")
            print(f"    - Count: {pagination.get('count')}")
        print()
        
        # Save to file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(script_dir, 'api_results.json')
        
        with open(output_file, 'w') as f:
            json.dump(api_data, f, indent=2)
        
        print(f"💾 Data saved to: {output_file}")
        print(f"   File size: {os.path.getsize(output_file) / 1024:.1f} KB")
        print()
        print("="*70)
        print("✓ Data fetch and save completed successfully!")
        print("="*70)
        
        return True
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Unable to reach Aviation Stack API")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Timeout Error: API request took too long")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
        return False
    except json.JSONDecodeError:
        print(f"❌ Error parsing API response as JSON")
        return False
    except IOError as e:
        print(f"❌ Error writing to file: {e}")
        return False


def main():
    """Interactive timetable data fetcher."""
    
    print("\nFetch options:")
    print("1. Fetch arrival timetables (no filters)")
    print("2. Fetch departure timetables (no filters)")
    print("3. Fetch arrivals for specific IATA airport code")
    print("4. Fetch departures for specific IATA airport code")
    print("5. Exit")
    
    choice = input("\nSelect option (1-5): ").strip()
    
    timetable_type = 'arrival'
    iata_code = None
    
    if choice == '1':
        print("\n(Fetching arrival timetables...)")
        fetch_and_save_timetable_data('arrival')
    
    elif choice == '2':
        print("\n(Fetching departure timetables...)")
        fetch_and_save_timetable_data('departure')
    
    elif choice == '3':
        iata_code = input("Enter IATA airport code (e.g., JFK): ").strip().upper()
        if iata_code:
            fetch_and_save_timetable_data('arrival', iata_code=iata_code)
        else:
            print("❌ No airport code provided")
    
    elif choice == '4':
        iata_code = input("Enter IATA airport code (e.g., JFK): ").strip().upper()
        if iata_code:
            fetch_and_save_timetable_data('departure', iata_code=iata_code)
        else:
            print("❌ No airport code provided")
    
    elif choice == '5':
        print("Exiting...")
        return
    
    else:
        print("❌ Invalid option")
        return


if __name__ == "__main__":
    main()
