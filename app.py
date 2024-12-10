from flask import Flask, Response, request, render_template, redirect, url_for, session, jsonify, redirect, url_for
import mysql.connector
import json
from geopy import distance

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Set a secret key for session management

# Database connection function
def connect_to_database():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        database="",  # Your database name
        user="",  # Your database username
        password="",  # Your database password
        autocommit=True
    )

# Get player data from database
def get_player_data(cursor, username):
    query = "SELECT * FROM player WHERE username = %s"
    cursor.execute(query, (username,))
    return cursor.fetchone()

# Initialize a new player
def initialize_player(cursor, username):
    query = """
    INSERT INTO player (username, completed_goals, visited_airports, continents_visited, flights_remaining) 
    VALUES (%s, '[]', '[]', '[]', 30);
    """
    cursor.execute(query, (username,))

# Medal mapping based on the number of completed goals
MEDAL_MAPPING = {
    0: "No rewards",
    1: "Bronze",
    2: "Silver",
    3: "Gold",
    4: "Platinum",
}

# Function to get all goals from the database (name and description)
def get_goals(cursor):
    query = "SELECT id, name, description FROM goal"
    cursor.execute(query)
    return cursor.fetchall()

# Update the player's completed goals when they complete a goal
def update_completed_goals(cursor, username, goal_name):
    # Get current completed goals
    cursor.execute("SELECT completed_goals FROM player WHERE username = %s", (username,))
    current_goals = cursor.fetchone()

    if current_goals:
        completed_goals = json.loads(current_goals[0])
        if goal_name not in completed_goals:
            completed_goals.append(goal_name)  # Add the completed goal
            completed_goals_json = json.dumps(completed_goals)

            # Update the player's completed goals in the database
            cursor.execute("UPDATE player SET completed_goals = %s WHERE username = %s",
                           (completed_goals_json, username))

# Modify display_status to include goal descriptions, completion status, and visited countries with coordinates
def display_status(player_data, cursor):
    completed_goals = json.loads(player_data[2])
    visited_airports = json.loads(player_data[3])
    continents_visited = json.loads(player_data[4])

    # Get all goals
    goals = get_goals(cursor)

    # Determine reward using the MEDAL_MAPPING
    reward = MEDAL_MAPPING.get(len(completed_goals), "Platinum")

    # Prepare goal data to send to the template
    goal_status = []
    for goal in goals:
        goal_name = goal[1]
        goal_description = goal[2]
        is_completed = "Completed" if goal_name in completed_goals else "Not completed"
        goal_status.append({
            "name": goal_name,
            "description": goal_description,
            "status": is_completed
        })

    # Fetch the coordinates of the visited countries
    visited_country_coordinates = []
    for country in visited_airports:
        cursor.execute("SELECT latitude, longitude FROM country WHERE name = %s", (country,))
        result = cursor.fetchone()
        if result:
            latitude, longitude = result
            visited_country_coordinates.append({
                "country": country,
                "latitude": latitude,
                "longitude": longitude
            })

    # Fetch the airport name where ident matches the last_airport
    cursor.execute("SELECT name FROM airport WHERE ident = %s", (player_data[6],))
    airport_result = cursor.fetchone()
    last_airport_name = airport_result[0] if airport_result else None

    return {
        "username": player_data[1],
        "completed_goals": completed_goals,
        "visited_airports": visited_airports,
        "continents_visited": continents_visited,
        "flights_remaining": player_data[5],
        "last_airport": player_data[6],
        "last_airport_name": last_airport_name,  # Include the name of the last airport
        "reward": reward,
        "goal_status": goal_status,  # This will be sent to the template
        "visited_country_coordinates": visited_country_coordinates  # Include visited countries' coordinates
    }


@app.route("/get_visited_country_coordinates", methods=["GET"])
def get_visited_country_coordinates():
    # Get the username from the session
    username = session.get("username")

    if not username:
        return json.dumps({"error": "User is not logged in"}), 400, {'Content-Type': 'application/json'}

    conn = connect_to_database()
    cursor = conn.cursor()

    # Fetch player data
    player_data = get_player_data(cursor, username)
    if not player_data:
        return json.dumps({"error": "Player not found"}), 404, {'Content-Type': 'application/json'}

    # Call the existing `display_status` function to get the visited country coordinates
    status = display_status(player_data, cursor)
    visited_country_coordinates = status["visited_country_coordinates"]  # This contains the visited country coordinates

    return json.dumps(visited_country_coordinates), 200, {'Content-Type': 'application/json'}


@app.route("/get_last_airport", methods=["GET"])
def get_last_airport():
    # Get the username from the session
    username = session.get("username")

    if not username:
        return json.dumps({"error": "User is not logged in"}), 400, {'Content-Type': 'application/json'}

    conn = connect_to_database()
    cursor = conn.cursor()

    # Fetch player data
    player_data = get_player_data(cursor, username)
    if not player_data:
        return json.dumps({"error": "Player not found"}), 404, {'Content-Type': 'application/json'}

    last_airport_icao = player_data[6]

    # Fetch the latitude, longitude, name, and iso_country of the last airport from the airport table
    cursor.execute("SELECT latitude_deg, longitude_deg, name, iso_country FROM airport WHERE ident = %s",
                   (last_airport_icao,))
    result = cursor.fetchone()

    if result:
        latitude, longitude, name, iso_country = result

        # Fetch the country name using the iso_country code
        cursor.execute("SELECT name FROM country WHERE iso_country = %s", (iso_country,))
        country_result = cursor.fetchone()

        country_name = country_result[0] if country_result else "Unknown"

        response = {
            "last_airport": last_airport_icao,
            "latitude_deg": latitude,
            "longitude_deg": longitude,
            "name": name,
            "country": country_name,
        }

        return json.dumps(response), 200, {'Content-Type': 'application/json'}
    else:
        return json.dumps({"error": "Last airport not found in database"}), 404, {'Content-Type': 'application/json'}


@app.route("/get_game_status", methods=["GET"])
def get_game_status():
    username = session.get("username")

    # Debug: Check session state
    print("Debug: Session state:", session)

    if not username:
        return json.dumps({"error": "User is not logged in"}), 400, {'Content-Type': 'application/json'}

    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # Debug: Database connection established
        print("Debug: Database connection established.")

        # Fetch player data
        player_data = get_player_data(cursor, username)

        # Debug: Log player data
        print("Debug: Player data retrieved:", player_data)

        if not player_data:
            return json.dumps({"error": "Player not found"}), 404, {'Content-Type': 'application/json'}

        # Extract fields
        user_flights_remaining = player_data[5]
        user_completed_goals = []
        if player_data[2]:
            try:
                user_completed_goals = json.loads(player_data[2])
            except json.JSONDecodeError as e:
                print("Error decoding completed goals:", e)

        # Debug: Log parsed values
        print("Debug: Flights remaining:", user_flights_remaining)
        print("Debug: Completed goals:", user_completed_goals)

        response = {
            "flights_remaining": user_flights_remaining,
            "completed_goals": user_completed_goals
        }

        return json.dumps(response), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        # Log the error for debugging
        print("Error in /get_game_status:", e)
        return json.dumps({"error": "Internal server error"}), 500, {'Content-Type': 'application/json'}


# Route to handle the goal completion
@app.route("/complete_goal", methods=["POST"])
def complete_goal():
    conn = connect_to_database()
    cursor = conn.cursor()

    username = request.form["username"]
    goal_name = request.form["goal_name"]

    # Update the completed goals
    update_completed_goals(cursor, username, goal_name)

    # Redirect to the player's status page
    return redirect(url_for("main", username=username))

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
    # Get the coordinates of the current location (e.g., airport)
    current_coords = a_b_distance(cursor, current_location_icao)

    if not current_coords:
        print("Current airport coordinates not found!")
        return []

    # Query to get airports in other countries, with coordinates taken from the country table
    query = """
    SELECT airport.ident, airport.name, country.latitude AS country_latitude, 
           country.longitude AS country_longitude, country.name AS country_name, 
           country.continent, country.iso_country 
    FROM airport
    INNER JOIN country ON airport.iso_country = country.iso_country
    WHERE airport.ident != %s 
    AND country.latitude IS NOT NULL AND country.longitude IS NOT NULL
    AND airport.type IN ('large_airport', 'medium_airport')  -- Only include large or medium airports
    """
    cursor.execute(query, (current_location_icao,))
    airports = cursor.fetchall()

    country_distances = {}

    for airport in airports:
        airport_icao, airport_name, country_lat, country_lon, airport_country, airport_continent, iso_country = airport
        airport_coords = (country_lat, country_lon)

        if airport_country not in country_distances:
            dist = distance.distance(current_coords, airport_coords).km
            country_distances[airport_country] = (dist, airport_continent, iso_country)

    # Sort the countries by distance and return the top closest
    sorted_countries = sorted(country_distances.items(), key=lambda x: x[1][0])
    return sorted_countries  # Return sorted countries by distance


# Function to get airports within a selected country
def get_airports_in_country(cursor, country_name):
    query = """
    SELECT airport.ident, airport.name, airport.latitude_deg, airport.longitude_deg
    FROM airport 
    INNER JOIN country ON airport.iso_country = country.iso_country
    WHERE country.name = %s 
    AND airport.type IN ('large_airport', 'medium_airport') 
    AND airport.latitude_deg IS NOT NULL AND airport.longitude_deg IS NOT NULL
    """
    cursor.execute(query, (country_name,))
    return cursor.fetchall()
#SELECT country.name AS "Country", count(airport.name) AS "Airport_count" FROM country INNER JOIN airport ON airport.iso_country = country.iso_country GROUP BY country.name ORDER BY country.name ASC;
# Route to handle login
@app.route("/", methods=["GET", "POST"])
def index():
    conn = connect_to_database()
    cursor = conn.cursor()


    if request.method == "POST":
        username = request.form["username"]

        # Store the username in session
        session["username"] = username

        # Check if username exists
        player_data = get_player_data(cursor, username)

        if player_data is None:
            # Initialize new player
            initialize_player(cursor, username)
            conn.commit()

            # Get the initialized player data to generate the status
            player_data = get_player_data(cursor, username)
            status = display_status(player_data, cursor)  # Generate status for the new player

            # Render the template for the new user with the initialized status
            return render_template("main.html", new_user=True, username=username, status=status)

        else:
            # Existing player, show their status
            status = display_status(player_data, cursor)

            return render_template("main.html", new_user=False, username=username, status=status)


    return render_template("index.html")


@app.route("/get_nearby_countries", methods=["POST"])
def get_nearby_countries_endpoint():
    data = request.json
    app.logger.debug(f"Request data: {data}")

    icao = data.get("icao")
    if not icao:
        return json.dumps({"error": "ICAO code is required"}), 400

    conn = connect_to_database()
    cursor = conn.cursor()

    app.logger.debug(f"Fetching nearby countries for ICAO: {icao}")
    try:
        sorted_countries = get_nearby_countries(cursor, icao)
        app.logger.debug(f"Nearby countries: {sorted_countries}")
    except Exception as e:
        app.logger.error(f"Error fetching nearby countries: {e}")
        return json.dumps({"error": "An error occurred"}), 500

    response = []
    for country, (dist, continent, iso_country) in sorted_countries[:10]:
        app.logger.debug(f"Processing country: {country}")
        cursor.execute("""
            SELECT latitude, longitude 
            FROM country 
            INNER JOIN airport ON country.iso_country = airport.iso_country 
            WHERE country.name = %s LIMIT 1
        """, (country,))
        coords = cursor.fetchone()

        response.append({
            "country": country,
            "iso_country": iso_country,
            "distance": dist,
            "continent": continent,
            "coordinates": coords if coords else None
        })

    app.logger.debug(f"Final response: {response}")
    return json.dumps(response), 200, {'Content-Type': 'application/json'}



@app.route("/get_airports_in_country", methods=["POST"])
def get_airports_in_country_endpoint():
    data = request.json
    country_name = data.get("country")

    conn = connect_to_database()
    cursor = conn.cursor()


    airports = get_airports_in_country(cursor, country_name)


    response = sorted(
        [
            {"icao": airport[0], "name": airport[1], "latitude_deg": airport[2], "longitude_deg": airport[3]}
            for airport in airports
        ],
        key=lambda x: x["name"]
    )

    return json.dumps(response), 200, {'Content-Type': 'application/json'}



@app.route('/icao', methods=['POST'])
def handle_icao():
    data = request.get_json()
    icao_code = data.get('icao_code')

    if not icao_code:
        return jsonify({"error": "ICAO code is required!"}), 400


    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT iso_country, continent FROM airport WHERE ident = %s", (icao_code,))
        airport = cursor.fetchone()

        if not airport:
            return jsonify({"error": "Airport with this ICAO code not found!"}), 404

        iso_country, continent = airport

        cursor.execute("SELECT name, continent FROM country WHERE iso_country = %s", (iso_country,))
        country = cursor.fetchone()

        if not country:
            return jsonify({"error": "Country not found for this ICAO code!"}), 404

        country_name, country_continent = country


        username = session.get("username")
        if not username:
            return jsonify({"error": "User not logged in!"}), 403

        cursor.execute("SELECT visited_airports, continents_visited, flights_remaining, completed_goals, last_airport FROM player WHERE username = %s", (username,))
        player = cursor.fetchone()

        if not player:
            return jsonify({"error": "Player not found!"}), 404

        visited_airports = json.loads(player[0]) if player[0] else []
        continents_visited = json.loads(player[1]) if player[1] else []
        flights_remaining = player[2] if player[2] is not None else 0
        completed_goals = json.loads(player[3]) if player[3] else []
        last_airport = player[4]


        last_airport = icao_code


        if continent and continent not in continents_visited:
            continents_visited.append(continent)

        if country_name not in visited_airports:
            visited_airports.append(country_name)


        asian_countries_visited = 0
        european_countries_visited = 0

        for visited_country in visited_airports:
            cursor.execute("SELECT continent FROM country WHERE name = %s", (visited_country,))
            country_info = cursor.fetchone()
            if country_info:
                country_continent = country_info[0]
                if country_continent == "AS":
                    asian_countries_visited += 1
                elif country_continent == "EU":
                    european_countries_visited += 1


        if asian_countries_visited >= 3 and "Visit Asian Countries" not in completed_goals:
            completed_goals.append("Visit Asian Countries")

        if european_countries_visited >= 3 and "Visit European Countries" not in completed_goals:
            completed_goals.append("Visit European Countries")

        if len(continents_visited) >= 4 and "Travel to Different Continents" not in completed_goals:
            completed_goals.append("Travel to Different Continents")

        if len(continents_visited) >= 7 and "Complete World Tour" not in completed_goals:
            completed_goals.append("Complete World Tour")


        if flights_remaining > 0:
            flights_remaining -= 1


        reward = MEDAL_MAPPING.get(len(completed_goals), "Platinum")


        cursor.execute(""" 
            UPDATE player 
            SET visited_airports = %s, last_airport = %s, continents_visited = %s, flights_remaining = %s, completed_goals = %s 
            WHERE username = %s
        """, (json.dumps(visited_airports), last_airport, json.dumps(continents_visited), flights_remaining, json.dumps(completed_goals), username))

        conn.commit()


        return jsonify({
            "message": "Player visited airports, last airport, continents visited, flights remaining, and completed goals updated successfully!",
            "visited_airports": visited_airports,
            "continents_visited": continents_visited,
            "flights_remaining": flights_remaining,
            "completed_goals": completed_goals,
            "previous_goals": json.loads(player[3]) if player[3] else [],
            "username": username,
            "last_airport": last_airport,
            "reward": reward
        })

    finally:
        cursor.close()
        conn.close()


@app.route('/reset-progress', methods=['POST'])
def reset_progress():

    username = session.get('username')

    if not username:
        return jsonify({'success': False, 'message': 'User not logged in.'})


    query = """
    UPDATE player
    SET completed_goals = '[]', 
        visited_airports = '[]', 
        continents_visited = '[]', 
        last_airport = NULL,
        flights_remaining = 30
    WHERE username = %s;
    """


    try:
        conn = connect_to_database()

        if conn is None:
            return jsonify({'success': False, 'message': 'Database connection failed.'})

        cursor = conn.cursor()


        cursor.execute(query, (username,))


        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': 'Player not found or no changes made.'})


        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Player progress reset successfully.'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while resetting progress.'})

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
