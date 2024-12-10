# Global Explorer

---

## Getting Started

Follow the instructions below to set up and run the game.

### Prerequisites

Ensure you have the following installed on your system:

1. Python 3.8+
2. MySQL Server: Set up MySQL on your system. First use globalexplorer_dataset.sql to initialize the database schema and data.
3. Required Python packages/imports:

```bash
from flask import Flask, Response, request, render_template, redirect, url_for, session, jsonify, redirect, url_for
import mysql.connector
import json
from geopy import distance
```

---

### Cloning the Repository

To get started, clone this repository:

Replace <your-username> with your GitHub profile username.

```bash
git clone https://github.com/<your-username>/GlobalExplorer.git
cd GlobalExplorer
```

---

## Database Setup

### Create Database & Populate

1. Open a terminal.
2. Login to your SQL server:

```bash
mysql -u <username> -p
```
or

```bash
mysql -u root -p
```

3. Create and select the database if not already created:
   
```bash
CREATE DATABASE globalexplorer;
USE globalexplorer;
```

4. Import the SQL file:

Remember to replace /path/to with the path of the globalexplorer_dataset.sql. 

```bash
SOURCE /path/to/globalexplorer_dataset.sql;
```

### Migrate Country Coordinates

Run the reading_country-coord.py script in Database_datasets along with the country-coord.csv file to populate the database with updated country coordinates:

```bash
python reading_country-coord.py
```

### Install Dependencies

Install the required Python packages:

```bash
pip install Flask mysql-connector-python geopy
```

Run the Flask application:

```bash
python app.py
```

---

## Run

Once the Flask server is running, open your browser and navigate to:

```bash
http://127.0.0.1:5000
```









