import requests
import json

params = {
  'access_key': 'e20e7bed45a2ceacb137580a8dae223f'
}

api_result = requests.get('https://api.aviationstack.com/v1/flights', params)

api_response = api_result.json()

# Function to search for flight by number
def get_flight_by_number(flights_data, flight_number):
    """Get all flights matching a specific flight number"""
    matching_flights = []
    for flight in flights_data['data']:
        if flight['flight']['number'] == flight_number:
            matching_flights.append(flight)
    return matching_flights

# Function to search for flight by IATA code (e.g., "NH1605")
def get_flight_by_iata(flights_data, iata_code):
    """Get all flights matching a specific IATA code"""
    matching_flights = []
    for flight in flights_data['data']:
        if flight['flight']['iata'] == iata_code:
            matching_flights.append(flight)
    return matching_flights

# Example: Get all data for flight number "5710"
flight_number = "5710"
results = get_flight_by_number(api_response, flight_number)

print(f"\n=== All flights with number {flight_number} ===")
print(f"Found {len(results)} flight(s)\n")

for idx, flight in enumerate(results, 1):
    print(f"Flight {idx}:")
    print(json.dumps(flight, indent=2))
    print("-" * 80)

# Example: Get flight by IATA code
iata_code = "NH1605"
results_iata = get_flight_by_iata(api_response, iata_code)

print(f"\n=== All data for IATA flight code {iata_code} ===")
for flight in results_iata:
    print(json.dumps(flight, indent=2))