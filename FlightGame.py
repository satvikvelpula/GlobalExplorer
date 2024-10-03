from geopy import distance
import mysql.connector
import json

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
def a_b_distance(cursor, icao):
    sql = "SELECT latitude_deg, longitude_deg FROM airport WHERE ident = %s"
    cursor.execute(sql, (icao,))
    result = cursor.fetchone()
    if result:
        latitude, longitude = result
        return latitude, longitude
    else:
        return None

# Function to get the country name and continent code by ICAO code
def get_country_and_continent(cursor, icao):
    sql = """
    SELECT country.name, country.continent 
    FROM airport 
    INNER JOIN country ON airport.iso_country = country.iso_country 
    WHERE airport.gps_code = %s
    """
    cursor.execute(sql, (icao,))
    result = cursor.fetchone()
    return result if result else (None, None)

# Function to get the nearby countries based on the current airport's location
def get_nearby_countries(cursor, current_location_icao):
    current_coords = a_b_distance(cursor, current_location_icao)

    if not current_coords:
        print("Current airport coordinates not found!")
        return []

    # Query to get airports in other countries
    query = """
    SELECT airport.ident, airport.name, airport.latitude_deg, airport.longitude_deg, country.name, country.continent 
    FROM airport
    INNER JOIN country ON airport.iso_country = country.iso_country
    WHERE airport.ident != %s AND airport.latitude_deg IS NOT NULL AND airport.longitude_deg IS NOT NULL
    """
    cursor.execute(query, (current_location_icao,))
    airports = cursor.fetchall()

    country_distances = {}

    for airport in airports:
        airport_icao, airport_name, lat, lon, airport_country, airport_continent = airport
        airport_coords = (lat, lon)

        if airport_country not in country_distances:
            dist = distance.distance(current_coords, airport_coords).km
            country_distances[airport_country] = (dist, airport_continent)

    # Sort the countries by distance and return the top closest
    sorted_countries = sorted(country_distances.items(), key=lambda x: x[1][0])
    return sorted_countries  # Return sorted countries by distance

# Function to get airports within a selected country, limiting to large/medium airports
def get_airports_in_country(cursor, country_name):
    query = """
    SELECT airport.ident, airport.name 
    FROM airport 
    INNER JOIN country ON airport.iso_country = country.iso_country
    WHERE country.name = %s 
    AND airport.type IN ('large_airport', 'medium_airport') 
    AND airport.latitude_deg IS NOT NULL AND airport.longitude_deg IS NOT NULL
    """
    cursor.execute(query, (country_name,))
    return cursor.fetchall()

# Function to get goals
def get_goals(cursor):
    query = "SELECT id, name, description FROM goal"
    cursor.execute(query)
    return cursor.fetchall()

# Function to initialize player data
def initialize_player(cursor, username):
    query = """
    INSERT INTO player (username, completed_goals, visited_airports, continents_visited, flights_remaining) 
    VALUES (%s, '[]', '[]', '[]', 30);
    """
    cursor.execute(query, (username,))

# Function to get player data
def get_player_data(cursor, username):
    query = "SELECT * FROM player WHERE username = %s"
    cursor.execute(query, (username,))
    return cursor.fetchone()

# Function to update player data with goals tracking
def track_goals(player_data, chosen_country, chosen_continent):
    updated_goals = json.loads(player_data[2])  # completed_goals
    visited_airports = json.loads(player_data[3])  # visited_airports
    continents_visited = json.loads(player_data[4])  # continents_visited
    flights_remaining = player_data[5]

    # Check if continent is already visited
    if chosen_continent not in continents_visited:
        continents_visited.append(chosen_continent)

    # Update airports visited
    if chosen_country not in visited_airports:
        visited_airports.append(chosen_country)

    # Update completed goals based on the current player status
    # Count the number of unique countries visited in Europe and Asia
    unique_countries = set(visited_airports)

    european_countries = [country for country in unique_countries if get_country_continent(cursor, country) == 'EU']
    asian_countries = [country for country in unique_countries if get_country_continent(cursor, country) == 'AS']

    # Check goals for Europe
    if chosen_continent == 'EU' and len(european_countries) >= 3:
        if "Visit European Airports" not in updated_goals:
            updated_goals.append("Visit European Airports")

    # Check goals for Asia (Fix: at least 3 unique Asian countries)
    if chosen_continent == 'AS' and len(asian_countries) >= 3:
        if "Visit Asian Airports" not in updated_goals:
            updated_goals.append("Visit Asian Airports")

    # Check goals for traveling to multiple continents
    if len(set(continents_visited)) >= 4:
        if "Travel to Different Continents" not in updated_goals:
            updated_goals.append("Travel to Different Continents")

    if len(set(continents_visited)) == 7:  # Assuming 7 continents
        if "Complete World Tour" not in updated_goals:
            updated_goals.append("Complete World Tour")

    # Update player data
    return {
        'completed_goals': json.dumps(updated_goals),
        'visited_airports': json.dumps(visited_airports),
        'continents_visited': json.dumps(continents_visited),
        'flights_remaining': flights_remaining - 1,
    }

# Helper function to get the continent of a country by name
def get_country_continent(cursor, country_name):
    query = "SELECT continent FROM country WHERE name = %s"
    cursor.execute(query, (country_name,))
    result = cursor.fetchone()
    return result[0] if result else None

# Function to display player status
def display_status(player_data):
    completed_goals = json.loads(player_data[2])
    visited_airports = json.loads(player_data[3])
    continents_visited = json.loads(player_data[4])

    print(f"Player Status:")
    print(f"Username: {player_data[1]}")
    print(f"Countries visited: {', '.join(visited_airports)}")
    print(f"Continents visited: {', '.join(set(continents_visited))}")
    print(f"Completed goals: {', '.join(completed_goals)}")
    print(f"Flights remaining: {player_data[5]}")

# Function to check if all goals are completed
def all_goals_completed(player_data, total_goals):
    completed_goals = json.loads(player_data[2])  # Get completed goals
    return len(completed_goals) == total_goals  # Check if completed goals match total goals

# Main game logic
def play_game():
    global cursor
    conn = connect_to_database()
    cursor = conn.cursor()

    username = input("Enter your username: ")

    # Check if player already exists
    player_data = get_player_data(cursor, username)
    if player_data is None:
        # Initialize player data if new player
        initialize_player(cursor, username)
        player_data = get_player_data(cursor, username)
    else:
        print(f"Welcome back, {username}! Resuming your game...")

    icao = input("Give ICAO code (e.g., EFHK for Helsinki Vantaa): ").upper()

    # Fetch the airport using the ICAO code
    cursor.execute("SELECT ident, name FROM airport WHERE ident = %s", (icao,))
    start_airport = cursor.fetchone()

    if not start_airport:
        print(f"Airport with ICAO code {icao} not found.")
        return

    current_location_icao = start_airport[0]
    current_location_name = start_airport[1]

    print(f"Welcome to Airport Explorer: Global Challenge!\n")
    print(f"You are currently at {current_location_name} ({current_location_icao}).")

    # Get total goals count
    total_goals = len(get_goals(cursor))

    while player_data[5] > 0:  # Check flights_remaining
        # Show goals
        goals = get_goals(cursor)
        print("Goals:")
        for goal in goals:
            if goal[0] not in json.loads(player_data[2]):  # Check completed goals
                print(f"- {goal[1]}: {goal[2]}")

        # Display nearby countries
        print("\nNearby Countries:")
        nearby_countries = get_nearby_countries(cursor, current_location_icao)
        if not nearby_countries:
            print("No nearby countries found.")
            continue  # Exit loop if no nearby countries are found

        for idx, (country, (distance, continent)) in enumerate(nearby_countries):
            print(f"{idx + 1}. {country} ({continent}) - Distance: {distance:.2f} km")
            if idx == 9:
                break

        # User selects the country to fly to
        country_choice = input("\nChoose a country number to fly to or type 'status' to see your status: ")

        if country_choice.lower() == "status":
            display_status(player_data)
            continue

        try:
            country_choice = int(country_choice) - 1
            if country_choice < 0 or country_choice >= len(nearby_countries):
                print("Invalid country choice. The number is not on the list. Please try again.")
                continue  # Prompt user again to make a valid selection

            chosen_country = nearby_countries[country_choice][0]
            chosen_continent = nearby_countries[country_choice][1][1]

            # Show airports in the chosen country
            print(f"\nAirports in {chosen_country}:")
            airports = get_airports_in_country(cursor, chosen_country)

            if not airports:
                print(f"No airports found in {chosen_country}.")
                continue

            for idx, airport in enumerate(airports):
                print(f"{idx + 1}. {airport[1]} ({airport[0]})")

            # User selects an airport in the chosen country
            airport_choice = input("\nChoose an airport number to fly to: ")

            try:
                airport_choice = int(airport_choice) - 1
                if airport_choice < 0 or airport_choice >= len(airports):
                    print("Invalid airport choice. The number is not on the list. Please try again.")
                    continue

                # Fly to the selected airport
                chosen_airport = airports[airport_choice]
                print(f"Flying to {chosen_airport[1]} ({chosen_airport[0]}).")

                # Update player data and goals
                player_updates = track_goals(player_data, chosen_country, chosen_continent)
                cursor.execute(""" 
                    UPDATE player 
                    SET completed_goals = %s, 
                        visited_airports = %s, 
                        continents_visited = %s, 
                        flights_remaining = %s 
                    WHERE username = %s
                """, (player_updates['completed_goals'], player_updates['visited_airports'],
                      player_updates['continents_visited'], player_updates['flights_remaining'], username))

                player_data = get_player_data(cursor, username)  # Refresh player data
                current_location_icao = chosen_airport[0]  # Update current location

                # Check if all goals are completed
                if all_goals_completed(player_data, total_goals):
                    print("Congratulations! You've completed all the goals and won the game! You have earned a platinum reward!")
                    break  # End the game if all goals are completed

            except ValueError:
                print("Invalid input. Please enter a number.")

        except ValueError:
            print("Invalid input. Please enter a number.")

    if player_data[5] == 0:
        print("Game Over! You've run out of flights.")


if __name__ == "__main__":
    play_game()