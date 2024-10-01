### This is the most maintained edition of the game 30.09.2024

from geopy import distance
import mysql.connector

# Database connection
def connect_to_database():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        database="flight_game2",
        user="eku",
        password="password",
        autocommit=True
    )

# Function to get the latitude and longitude of an airport by ICAO code
def a_b_distance(icao):
    sql = f"SELECT latitude_deg, longitude_deg FROM airport WHERE ident = %s"
    cursor.execute(sql, (icao,))
    result = cursor.fetchone()
    if result:
        latitude, longitude = result
        return latitude, longitude
    else:
        return None

def get_country_by_icao(icao):
    sql = f"SELECT country.name FROM airport INNER JOIN country ON airport.iso_country = country.iso_country WHERE airport.gps_code = '{icao}'"
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute(sql)
    result = cursor.fetchone()

    if result:
        return result[0]

# Get nearby airports based on distance from the current location
def get_nearby_airports(current_location_icao, country):
    current_coords = a_b_distance(current_location_icao)

    if not current_coords:
        print("Current airport coordinates not found!")
        return []

    query = f"""
    SELECT airport.ident, airport.name FROM airport
    INNER JOIN country ON airport.iso_country = country.iso_country
    WHERE airport.ident != %s AND airport.latitude_deg IS NOT NULL AND airport.longitude_deg IS NOT NULL AND country.name = '{country}'
    """

    cursor.execute(query, (current_location_icao,))
    airports = cursor.fetchall()

    airport_distances = []
    #print(airports[0][1])
    for airport in airports:
        #print(airport[1])
        airport_split = airport[1].split()
        #print(airport_split)

        airport_icao, airport_name = airport
        airport_coords = a_b_distance(airport_icao)

        if airport_coords:
            if airport_split[-1] == "Airport":
                dist = distance.distance(current_coords, airport_coords).km
                airport_distances.append((airport_icao, airport_name, dist))

    # Sort by distance and return the 10 closest airports
    airport_distances.sort(key=lambda x: x[2])
    return airport_distances[:10]

# Get goal data
def get_goals():
    query = "SELECT id, name, description FROM goal"
    cursor.execute(query)
    return cursor.fetchall()

# Main game logic
def play_game():
    global cursor
    conn = connect_to_database()
    cursor = conn.cursor()

    icao = input("Give ICAO code (e.g., EFHK for Helsinki Vantaa): ").upper()

    # Fetch the airport using the ICAO code
    cursor.execute("SELECT ident, name FROM airport WHERE ident = %s", (icao,))
    start_airport = cursor.fetchone()

    if not start_airport:
        print(f"Airport with ICAO code {icao} not found.")
        return

    current_location_icao = start_airport[0]
    current_location_name = start_airport[1]

    # Game setup
    flights_remaining = 20
    goals = get_goals()
    completed_goals = []

    country = get_country_by_icao(icao)

    print(f"Welcome to Airport Explorer: Global Challenge!\n")
    print(f"You are currently at {current_location_name} ({current_location_icao}).")
    print(f"You have {flights_remaining} flights remaining.\n")

    while flights_remaining > 0:
        # Show goals
        print("Goals:")
        for goal in goals:
            if goal[0] not in completed_goals:
                print(f"- {goal[1]}: {goal[2]}")

        # Show nearby airports
        print(f"\nCurrent location ICAO code: {current_location_icao}")
        print("\nNearby Airports:")
        airports = get_nearby_airports(current_location_icao, country)

        for idx, airport in enumerate(airports):
            print(f"{idx + 1}. {airport[1]} ({airport[0]}) - Distance: {airport[2]:.2f} km")

        # Get user input
        choice = input("\nChoose an airport number to fly to (or type 'status' to check status, or type 'goals' to check remaining goals): ")

        if choice.lower() == 'status':
            print(f"\nCurrent Location: {current_location_name} ({current_location_icao})")
            print(f"Flights Remaining: {flights_remaining}")
            print("Goals Completed:", len(completed_goals))
            print()
            continue

        try:
            choice = int(choice) - 1
            if choice < 0 or choice >= len(airports):
                print("Invalid choice. Please try again.")
                continue
            chosen_airport = airports[choice]
            current_location_icao = chosen_airport[0]
            current_location_name = chosen_airport[1]
            flights_remaining -= 1
            print(f"\nFlying to {current_location_name} ({current_location_icao}). Flights remaining: {flights_remaining}")

            # Check if any goals are completed
            for goal in goals:
                if goal[0] not in completed_goals:
                    completed_goals.append(goal[0])

        except ValueError:
            print("Invalid input. Please enter a number.")

    print("\nGame Over!")
    print(f"You completed {len(completed_goals)} goals.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    play_game()