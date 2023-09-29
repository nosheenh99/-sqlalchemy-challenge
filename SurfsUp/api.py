# Import the dependencies.
import sqlalchemy

from datetime import datetime, timedelta

from flask import Flask, jsonify

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func


#################################################
# Database Setup
#################################################

# Create an instance of the SQL Engine
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
Base.prepare(autoload_with=engine)

# reflect the tables
Base.classes.keys()

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################

app = Flask(__name__)


#################################################
# Flask Routes
#################################################


# 1. /
# Start at the homepage.
# List all the available routes.
@app.route("/")
def home():
    """List all available api routes."""
    return jsonify(
        {
            "Available Routes": [
                "/api/v1.0/precipitation",
                "/api/v1.0/stations",
                "/api/v1.0/tobs",
                "/api/v1.0/<start>",
                "/api/v1.0/<start>/<end>",
            ]
        }
    )


# 2. /api/v1.0/precipitation
# Convert the query results from your precipitation analysis
# (i.e. retrieve only the last 12 months of data) to a dictionary using date as the key and prcp as the value.
# Return the JSON representation of your dictionary.
@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)

    # Find the most recent date in the data set
    recent_date = (
        session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    )

    # Calculate the date one year from the last date in data set
    one_year_ago = (
        datetime.strptime(recent_date[0], "%Y-%m-%d") - timedelta(days=365)
    ).strftime("%Y-%m-%d")

    # Perform a query to retrieve the data and precipitation scores
    results = (
        session.query(Measurement.date, Measurement.prcp)
        .filter(Measurement.date >= one_year_ago)
        .all()
    )

    session.close()

    # Create a dictionary from the row data and append to a list of all precipitation data
    precipitation_data = {date: prcp for date, prcp in results}

    return jsonify(precipitation_data)


# /api/v1.0/stations
# Return a JSON list of stations from the dataset.
@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)

    # Query all stations from the database
    results = session.query(Station.station, Station.name).all()

    session.close()

    # Create a list of dictionaries with the station data
    stations_list = [{"station": station, "name": name} for station, name in results]

    return jsonify(stations_list)


# /api/v1.0/tobs
# Query the dates and temperature observations of the most-active station for the previous year of data.
# Return a JSON list of temperature observations for the previous year
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)

    # Find the most active station
    most_active_station = (
        session.query(Measurement.station, func.count(Measurement.station))
        .group_by(Measurement.station)
        .order_by(func.count(Measurement.station).desc())
        .first()
        .station
    )

    # Find the most recent date in the data set
    recent_date = (
        session.query(Measurement.date).order_by(Measurement.date.desc()).first().date
    )

    # Calculate the date one year from the last date in data set
    one_year_ago = (
        datetime.strptime(recent_date, "%Y-%m-%d") - timedelta(days=365)
    ).strftime("%Y-%m-%d")

    # Query the last 12 months of temperature observation data for this station
    results = (
        session.query(Measurement.date, Measurement.tobs)
        .filter(Measurement.date >= one_year_ago)
        .filter(Measurement.station == most_active_station)
        .all()
    )

    session.close()

    # Create a list of dictionaries with the date and temperature data
    tobs_data = [{"date": date, "tobs": tobs} for date, tobs in results]

    return jsonify(tobs_data)


# /api/v1.0/<start>/
# Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature for a specified start or start-end range.
# For a specified start, calculate TMIN , TAVG , and TMAX for all the dates greater than or equal to the start date.
# For a specified start date and end date, calculate TMIN , TAVG , and TMAX for the dates from the start date to the end date, inclusive.
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def start_end(start=None, end=None):
    session = Session(engine)

    # Define the select query statement
    sel = [
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs),
    ]

    # If no end date is provided, query for all dates greater than or equal to the start date
    if not end:
        results = session.query(*sel).filter(Measurement.date >= start).all()

    # If an end date is provided, query for all dates between the start and end dates, inclusive
    else:
        results = (
            session.query(*sel)
            .filter(Measurement.date >= start)
            .filter(Measurement.date <= end)
            .all()
        )

    session.close()

    # Create a dictionary from the row data and append to a list of all_temp_stats
    temp_stats = []

    for Tmin, Tavg, Tmax in results:
        temp_stat_dict = {}

        temp_stat_dict["MIN TEMPERATURE"] = Tmin
        temp_stat_dict["AVG TEMPERATURE"] = Tavg
        temp_stat_dict["MAX TEMPERATURE"] = Tmax

        temp_stats.append(temp_stat_dict)

    return jsonify(temp_stats)


if __name__ == "__main__":
    app.run(debug=True)
