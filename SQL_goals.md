CREATE TABLE goal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    icon VARCHAR(255),
    target VARCHAR(255) NOT NULL,
    target_minvalue INT DEFAULT NULL,
    target_maxvalue INT DEFAULT NULL,
    target_text VARCHAR(255) DEFAULT NULL
);

INSERT INTO goal (name, description, icon, target, target_minvalue, target_maxvalue, target_text) VALUES
('Visit European Airports', 'Travel to at least 3 different airports in Europe.', 'europe_icon.png', 'airports_in_europe', 3, NULL, 'Visit 3 different airports located in Europe.'),
('Visit Asian Airports', 'Travel to at least 3 different airports in Asia.', 'asia_icon.png', 'airports_in_asia', 3, NULL, 'Visit 3 different airports located in Asia.'),
('Travel to Different Continents', 'Fly to airports in at least 4 different continents.', 'continents_icon.png', 'continents_visited', 4, NULL, 'Fly to airports located in 4 different continents.'),
('Complete World Tour', 'Complete a world tour by visiting airports on each continent.', 'world_tour_icon.png', 'world_tour_completed', 1, NULL, 'Visit at least one airport on every continent to complete the world tour.');


CREATE TABLE player (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) NOT NULL UNIQUE, completed_goals JSON NOT NULL, visited_airports JSON NOT NULL, continents_visited JSON NOT NULL, flights_remaining INT DEFAULT 30, last_airport VARCHAR(255));