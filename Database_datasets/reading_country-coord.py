import csv
import mysql.connector

DB_CONFIG = {
    "host": "127.0.0.1",  # Your database host
    "port": 3307,
    "user": "root",  # Your database username
    "password": "Metropolia05",
    "database": "flight_game",  # Your database name
}

CSV_FILE_PATH = "country-coord.csv"

MANUAL_UPDATES = {
    "BL": {"latitude": 17.9, "longitude": -62.83},   # St. Barthelemy
    "BQ": {"latitude": 12.2, "longitude": -68.26},  # Caribbean Netherlands
    "CW": {"latitude": 12.2, "longitude": -69.00},  # Curacao
    "MF": {"latitude": 18.07, "longitude": -63.056}, # Saint Martin
    "SX": {"latitude": 18.04, "longitude": -63.053}, # Sint Maarten
    "XK": {"latitude": 42.50, "longitude": 20.879},  # Kosovo
}

DELETE_COUNTRIES = ["ZZ"]

def ensure_columns_exist(cursor, conn):
    """
    Ensure that latitude and longitude columns exist in the country table.
    If not, add them.
    """
    try:
        # Check if 'latitude' and 'longitude' columns exist
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'country';
        """, (DB_CONFIG["database"],))
        existing_columns = {row[0] for row in cursor.fetchall()}

        # Add missing columns
        if 'latitude' not in existing_columns:
            cursor.execute("ALTER TABLE country ADD COLUMN latitude FLOAT;")
            print("Added 'latitude' column to the country table.")
        if 'longitude' not in existing_columns:
            cursor.execute("ALTER TABLE country ADD COLUMN longitude FLOAT;")
            print("Added 'longitude' column to the country table.")

        # Commit changes
        conn.commit()

    except mysql.connector.Error as e:
        print(f"Error checking or adding columns: {e}")


def apply_manual_updates(cursor):
    for iso_country, coords in MANUAL_UPDATES.items():
        latitude = coords["latitude"]
        longitude = coords["longitude"]
        try:
            query = """
                UPDATE country
                SET latitude = %s, longitude = %s
                WHERE iso_country = %s
            """
            cursor.execute(query, (latitude, longitude, iso_country))
            print(f"Manually updated {iso_country}.")
        except mysql.connector.Error as e:
            print(f"Error updating {iso_country}: {e}")


def delete_unwanted_countries(cursor):
    for iso_country in DELETE_COUNTRIES:
        try:
            query = "DELETE FROM country WHERE iso_country = %s"
            cursor.execute(query, (iso_country,))
            print(f"Deleted country with ISO code: {iso_country}")
        except mysql.connector.Error as e:
            print(f"Error deleting {iso_country}: {e}")

def delete_countries_without_airports(cursor):
    try:
        query = """
        DELETE c
        FROM country c
        LEFT JOIN airport a ON c.iso_country = a.iso_country
            AND a.type IN ('large_airport', 'medium_airport')
        WHERE a.iso_country IS NULL;
        """
        cursor.execute(query)
        print("Deleted countries without airports.")
    except mysql.connector.Error as e:
        print(f"Error deleting countries without airports: {e}")


def update_database_from_csv():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Ensure columns exist
        ensure_columns_exist(cursor, conn)

        # Process CSV file
        with open(CSV_FILE_PATH, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                iso_country = row["Alpha-2 code"]
                latitude = row["Latitude (average)"]
                longitude = row["Longitude (average)"]

                if iso_country and latitude and longitude:
                    try:
                        query = """
                            UPDATE country
                            SET latitude = %s, longitude = %s
                            WHERE iso_country = %s
                        """
                        cursor.execute(query, (latitude, longitude, iso_country))
                    except mysql.connector.Error as e:
                        print(f"Error updating {iso_country}: {e}")

        # Apply manual updates
        apply_manual_updates(cursor)

        # Delete unwanted countries
        delete_unwanted_countries(cursor)

        # Delete countries without airports
        delete_countries_without_airports(cursor)

        # Commit changes
        conn.commit()
        print("Database update complete!")

    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


if __name__ == "__main__":
    update_database_from_csv()