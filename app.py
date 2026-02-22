from flask import Flask, render_template, request, url_for, jsonify
import fastf1
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from visualizations.info import RaceResults, DriverTimingsFP, drivers_championship_table, constructors_championship_table, find_next_race_info, DriverTimingsQuali, DriverTimingsQualiSession, find_track_image
from visualizations.plots import (SpeedAcrossQualiLap,RacePOSChange,RaceLapTimePlot,TeamPaceComp,BrakePressure,ThrottleVSBrakePressure,DriverVSDriverStats,TyreStrategies,DriverLapTimes,DriverReactionTimes)
from visualizations.race import combined_plotly_race_dashboard, driver_vs_driver_pace_plot as dvdp_plot
from visualizations.lap_animation import DriverTelemetryVisualised, DriverVSDriverQuali

# Enable cache
fastf1.Cache.enable_cache("C:/Users/vivaa/F1/f1_dashboard/cache")

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    drivers_table = drivers_championship_table()
    constructors_table = constructors_championship_table()

    iso, gp_name, description, image_name = find_next_race_info()

    return render_template("home.html",
                           drivers_table=drivers_table,
                           constructors_table=constructors_table,
                           next_race_iso=iso,
                           next_race_name=gp_name,
                           next_race_description=description,
                           next_race_image=image_name)

@app.route('/results', methods=['POST'])
def results():
    year = int(request.form['year'])
    gp = request.form['gp']
    gp_name = gp
    session = request.form['session']

    if session in ["FP1", "FP2", "FP3"]:
        df = DriverTimingsFP(year, gp, session)
        table_html = df.to_html(classes="table table-striped table-hover text-center", index=False, border=0)
        track_img = find_track_image(year, gp)
        return render_template("index_fp.html",year=year, gp_name=gp_name , session=session , table=table_html, track_img=track_img)

    elif session == "R":
        # Table of results
        df = RaceResults(year, gp)
        table_html = df.to_html(classes="table table-striped table-hover text-center", index=False, border=0)
        track_img = find_track_image(year, gp)
        # Generate combined Plotly dashboard (interactive)
        plots_html = combined_plotly_race_dashboard(year, gp)
        # Generate trye strategy plot
        tyre_strat = TyreStrategies(year, gp) 
        # Load session
        sess = fastf1.get_session(year, gp, "R")
        sess.load(telemetry=False, weather=False)
        # Correcting driver identification
        drivers = [sess.get_driver(d)["Abbreviation"] for d in sess.drivers]

        return render_template(
            "index_race.html",
            year=year,
            gp=gp_name,
            gp_name=gp_name,
            session=session,
            table=table_html,
            plots_html=plots_html,
            tyre_strat=tyre_strat,
            drivers = drivers,
            track_img=track_img

        )

    elif session == "Q":
        print("QUALI BLOCK RUNNING")
        # Get overall quali times 
        df = DriverTimingsQuali(year, gp)
        # Get quali session by session times 
        qs_df = DriverTimingsQualiSession(year,gp)
        # Get track image
        track_img = find_track_image(year, gp)

        # Load session
        sess = fastf1.get_session(year, gp, "Q")
        sess.load(telemetry=False)

        drivers = []
        for d in sess.drivers:
            print("Driver code:", d)
            info = sess.get_driver(d)
            print("Driver info:", info)
            drivers.append(info["Abbreviation"])

        print("Final drivers list:", drivers)

        table_html = df.to_html(classes="table table-striped table-hover text-center", index=False, border=0)
        qs_table_html = qs_df.to_html(classes="table table-striped table-hover text-center", index=False, border=0)
        return render_template("index_quali.html",year=year, gp_name=gp , session=session , table=table_html, qstable = qs_table_html, track_img=track_img,drivers=drivers)
    else:
        return "Invalid session", 400

@app.route("/driver_vs_driver_pace_plot", methods=["GET"])
def driver_vs_driver_pace_plot_route():
    year = int(request.args["year"])
    gp = request.args["gp"]
    driver_a = request.args["a"]
    driver_b = request.args["b"]

    data = dvdp_plot(
        year=year,
        grand_prix=gp,
        driver_A=driver_a,
        driver_B=driver_b
    )

    return jsonify(data)

@app.route("/telemetry")
def driver_telemetry_visualised_backend():
    year = int(request.args["year"])
    gp = request.args["gp"]
    driver = request.args["driver"]

    data = DriverTelemetryVisualised(year,gp,driver)

    return data

@app.route("/driver_quali_lap_visualised")
def driver_quali_lap():
    year = request.args.get("year")
    gp = request.args.get("gp")
    driver = request.args.get("driver")

    return render_template(
        "driver_quali_lap.html",
        year=year,
        gp=gp,
        driver=driver
    )


if __name__ == "__main__":
    app.run(debug=True)