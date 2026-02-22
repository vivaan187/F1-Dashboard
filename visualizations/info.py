import fastf1
import pandas as pd
import fastf1.plotting
import matplotlib
matplotlib.use("Agg") # Prevents external Mat Plot Lib windows from opening
import matplotlib.pyplot as plt
from collections import defaultdict
from fastf1.ergast import Ergast
import requests
from bs4 import BeautifulSoup
import re
import datetime
import pytz
from flask import url_for
import os

# Enable cache
fastf1.Cache.enable_cache("C:/Users/vivaa/F1/f1_dashboard/cache")

# Drivers and Tracks list
drivers_list = ["LEC","HAM","NOR","PIA","VER","TSU","RUS","ANT","ALO","STR",
                "SAI","ALB","HUL","BOR","LAW","HAD","OCO","BEA","GAS","COL","DOO"]

tracks = ["Australia","China","Japan","Bahrain","Saudi Arabia","Miami","Emilia Romagna",
          "Monaco","Spain","Canada","Austria","Britain","Belgium","Hungary","Netherlands",
          "Italy","Baku","Singapore","United States","Mexico City","Sao Paulo","Las Vegas",
          "Qatar","Abu Dhabi"]

# Tools

# Changing normal time to time delta format
def format_timedelta(td):
    # Handle None, NaN, and strings
    if td is None or isinstance(td, str):
        return td if td not in [None, "NaT"] else "N/A"

    try:
        total_seconds = td.total_seconds()
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:06.3f}"
    except Exception:
        return "N/A"

def find_track_image(year: int,gp: str):
    # Get event schedule
    events = fastf1.get_event_schedule(year)
    print(year)
    # Find matching row
    print(gp)
    match = events[(events["EventName"] == gp) |
        (events["Country"] == gp)]

    if not match.empty:
        name = match.iloc[0]["Location"]
    else:
        raise ValueError(f"No event found matching {gp}")

    fname = name + ".png"
    track_img = fname

    return track_img


def DriverTimingsFP(year: int, gp: str, session_type: str):
    session = fastf1.get_session(year, gp, session_type)
    session.load()
    
    results = []

    for drv in session.drivers:
        drv_laps = session.laps.pick_drivers(drv)
        if drv_laps.empty:
            continue

        fastest = drv_laps.pick_fastest()
        if fastest is None or pd.isna(fastest["LapTime"]):
            continue  # skip drivers with no valid fastest lap

        drv_info = session.get_driver(drv)

        results.append({
            "Driver": drv_info["Abbreviation"],
            "Team": drv_info["TeamName"],
            "LapNumber": fastest["LapNumber"],
            "LapTime": pd.to_timedelta(fastest["LapTime"]),
            "Sector1": pd.to_timedelta(fastest["Sector1Time"]),
            "Sector2": pd.to_timedelta(fastest["Sector2Time"]),
            "Sector3": pd.to_timedelta(fastest["Sector3Time"]),
            "Compound": fastest["Compound"],
        })

    # Sort safely
    results = sorted(results, key=lambda x: x["LapTime"])

    # Make a pd dataframe
    df = pd.DataFrame(results)
    
    # Normalise time into minutes, seconds and milliseconds 
    df['LapTime'] = df['LapTime'].apply(format_timedelta)
    df['Sector1'] = df['Sector1'].apply(format_timedelta)
    df['Sector2'] = df['Sector2'].apply(format_timedelta)
    df['Sector3'] = df['Sector3'].apply(format_timedelta)

    return df

def DriverTimingsQuali(year: int, gp: str):
    session = fastf1.get_session(year, gp, "Q")
    session.load()
    
    results = []

    for drv in session.drivers:
        drv_laps = session.laps.pick_drivers(drv)
        if drv_laps.empty:
            continue

        fastest = drv_laps.pick_fastest()
        if fastest is None or pd.isna(fastest["LapTime"]):
            continue  # skip drivers with no valid fastest lap

        drv_info = session.get_driver(drv)

        results.append({
            "Driver": drv_info["Abbreviation"],
            "Team": drv_info["TeamName"],
            "LapNumber": fastest["LapNumber"],
            "LapTime": pd.to_timedelta(fastest["LapTime"]),
            "Sector1": pd.to_timedelta(fastest["Sector1Time"]),
            "Sector2": pd.to_timedelta(fastest["Sector2Time"]),
            "Sector3": pd.to_timedelta(fastest["Sector3Time"]),
            "Compound": fastest["Compound"],
        })

    # Sort safely
    results = sorted(results, key=lambda x: x["LapTime"])

    # Make a pd dataframe
    df = pd.DataFrame(results)
    
    # Normalise time into minutes, seconds and milliseconds 
    df['LapTime'] = df['LapTime'].apply(format_timedelta)
    df['Sector1'] = df['Sector1'].apply(format_timedelta)
    df['Sector2'] = df['Sector2'].apply(format_timedelta)
    df['Sector3'] = df['Sector3'].apply(format_timedelta)

    return df

def DriverTimingsQualiSession(year: int, grand_prix: str):
    # Load race session
    session = fastf1.get_session(year, grand_prix, 'Q')
    session.load()

    times = []

    # Classification already sorted by position
    for _, row in session.results.iterrows():
        drv = row['Abbreviation']
        team = row['TeamName']
        pos = row['Position']
        # All quali session times
        q1 = row['Q1']
        q2 = row['Q2']
        q3 = row['Q3']

        times.append({
            'Pos': pos,
            'Driver': drv,
            'Team': team,
            'Q1 time': q1,
            'Q2 time': q2,
            'Q3 time': q3
        })
    
    # Create a pd dataframe
    qs_df = pd.DataFrame(times)
    # Normlise quali timings
    qs_df['Q1 time'] = qs_df['Q1 time'].apply(format_timedelta)
    qs_df['Q2 time'] = qs_df['Q2 time'].apply(format_timedelta)
    qs_df['Q3 time'] = qs_df['Q3 time'].apply(format_timedelta)

    return qs_df

def RaceResults(year: int, gp: str):
    # Load race session
    session = fastf1.get_session(year, gp, "R")
    session.load()

    results = []

    # Classification already sorted by position
    for _, row in session.results.iterrows():
        drv = row['Abbreviation']
        team = row['TeamName']
        pos = row['Position']
        interval = row['Time']  # Interval from leader
        status = row['Status']  # Finished, DNF, DSQ, etc.

        # Get fastest lap + last tyre
        drv_laps = session.laps.pick_drivers(drv)
        if len(drv_laps) > 1:
            best_lap = drv_laps.pick_fastest()
            if best_lap is None or best_lap.empty:
                best_lap = None
            if best_lap is not None and 'LapTime' in best_lap:
                best_time = best_lap['LapTime']
            else:
                best_time = "N/A"
            finish_tyre = drv_laps.iloc[-1]['Compound']  # last used compound
        else:
            best_time = None
            finish_tyre = None

        results.append({
            "Pos": pos,
            "Driver": drv,
            "Team": team,
            "BestLap": best_time,
            "FinishingTyre": finish_tyre,
            "Interval": interval,
            "Status": status
        })

    # Make a pd dataframe
    race_df = pd.DataFrame(results)

    # Normalise time into minutes, seconds and milliseconds 
    race_df['BestLap'] = race_df['BestLap'].apply(format_timedelta)
    race_df['Interval'] = race_df['Interval'].apply(format_timedelta)

    return race_df

def drivers_championship_table():
    # Call ergast as an internal function rather than public
    ergast = Ergast()
    # Get standings
    DriverPoints = ergast.get_driver_standings(season=2025, round=24)
    drivers_standings = DriverPoints.content[0]

    df = pd.DataFrame(drivers_standings)
    df = df[['position', 'points', 'driverNumber', 'familyName', 'constructorNames']]  # Keep only required columns
    df = df.rename(columns={
        'position': 'Position',
        'points': 'Points',
        'driverNumber': 'Number',
        'familyName': 'Driver',
        'constructorNames': 'Team'
    })

    return df.to_html(classes="championship-table", index=False, border=0)

def constructors_championship_table():
    # Call ergast as an internal function rather than public
    ergast = Ergast()
    # Get standings
    ConstructorsPoints = ergast.get_constructor_standings(season=2025,round=24)
    constructors_standings = ConstructorsPoints.content[0]

    df = pd.DataFrame(constructors_standings)
    df = df[['position', 'points', 'constructorName']]
    df = df.rename(columns={
        'position': 'Position',
        'points': 'Points',
        'constructorName': 'Constructor'
    })

    return df.to_html(classes="championship-table", index=False, border=0)


def find_next_race_info(year=None):
    """
    Returns (iso_utc_str, gp_display_name, description, image_name_or_none)
    """
    now_utc = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
    current_year = datetime.datetime.now().year
    years_to_check = [current_year, current_year + 1] if year is None else [year]

    for y in years_to_check:
        sched = fastf1.get_event_schedule(y)
        if sched.empty:
            continue

        # Try to find datetime column
        date_col = None
        for c in sched.columns:
            if any(k in c.lower() for k in ("date", "start")):
                date_col = c
                break
        if date_col is None:
            for c in sched.columns:
                if pd.api.types.is_datetime64_any_dtype(sched[c]):
                    date_col = c
                    break
        if date_col is None:
            continue

        # Normalize to datetime (UTC)
        try:
            sched[date_col] = pd.to_datetime(sched[date_col], errors="coerce", utc=True)
        except Exception:
            sched[date_col] = pd.to_datetime(sched[date_col], errors="coerce")

        future_rows = sched[sched[date_col] > now_utc]
        if future_rows.empty:
            continue

        next_row = future_rows.sort_values(by=date_col).iloc[0]

        # Find GP name (display)
        gp_name = None
        for col in ("EventName", "Event", "name", "Event_LongName","Location"):
            if col in sched.columns and pd.notna(next_row.get(col)):
                gp_name = next_row.get(col)
                break
        if not gp_name:
            for v in next_row:
                if isinstance(v, str) and v.strip():
                    gp_name = v.strip()
                    break
        if not gp_name:
            continue

        # Ensure tz-aware datetime -> iso
        next_dt = next_row[date_col]
        if pd.isna(next_dt):
            continue
        if getattr(next_dt, "tzinfo", None) is None:
            next_dt = pytz.UTC.localize(next_dt)
        iso = next_dt.astimezone(pytz.UTC).isoformat()

        # Get description (case-insensitive)
        desc = ""
        for k, v in TRACK_DESCRIPTIONS.items():
            if k.strip().lower() == str(gp_name).strip().lower():
                desc = v
                break

        # Get event schedule
        events = fastf1.get_event_schedule(y)

        # Find matching row
        match = events[events["EventName"] == gp_name]

        if not match.empty:
            name = match.iloc[0]["Location"]
        else:
            raise ValueError(f"No event found matching {gp_name}")

        fname = name + ".png"
        image_name = fname

        return iso, gp_name, desc, image_name

    return "", "", "", None

def find_track_stats():
    remaining_events = fastf1.get_events_remaining()

    next_race = remaining_events.iloc[0]

    next_race["Ra"]

TRACK_DESCRIPTIONS = {
    "Australian Grand Prix": "The Australian Grand Prix kicks off the season at Melbourne’s Albert Park, combining parkland road sections with high-speed straights. It’s known for unpredictable weather and tight margins in early-season performance.",
    "Chinese Grand Prix": "Held at the Shanghai International Circuit, this GP features a long back straight and sweeping turns that reward balance and top speed. Expect overtaking opportunities along the main straight and in slow corners.",
    "Japanese Grand Prix": "Taking place at the iconic Suzuka circuit with its unique figure-8 layout and sweeping high speed corners, the Japanese Grand Prix demands driver perfection. The difficult layout and variable weather make it an exciting technical challenge.",
    "Bahrain Grand Prix": "A night race between the desert dunes, the Bahrain Grand Prix is a nail-biting thriller with intense wheel-to-wheel action. Watch for brave lunges into Turn 1 and long wheel to wheel battles in the middle sector.",
    "Saudi Arabian Grand Prix": "The walls envelope the drivers as they speed at high speed through the Jeddah Corniche Circuit. It rewards brave driving but punishes mistakes.",
    "Miami Grand Prix": "The Miami Grand Prix runs through a modern temporary circuit with stadium-like viewing and long straights. The track surface and grip can change during the weekend, producing variable race pace.",
    "Emilia Romagna Grand Prix": "Imola features fast, interconnected corners set against Italian countryside. It mixes flowing sequences and technical sections, rewarding precision.",
    "Monaco Grand Prix": "The crown jewel street race through Monte Carlo is tight and unforgiving. Precision, qualifying and track position dominate the outcome.",
    "Spanish Grand Prix": "Barcelona-Catalunya is a long-established test track with a mix of medium and high-speed corners. Teams use it as a baseline to compare car performance.",
    "Canadian Grand Prix": "Circuit Gilles-Villeneuve pairs long straights with slow chicanes and close walls. It is notorious for late-race drama and the 'Wall of Champions'.",
    "Austrian Grand Prix": "The Red Bull Ring is compact with elevation changes and short lap times. It rewards strong engine performance and braking.",
    "British Grand Prix": "Silverstone is the 'Home of British Motor Racing' with high-speed sweeping corners. It demands aero efficiency and driver stamina.",
    "Belgian Grand Prix": "Spa-Francorchamps is long, flowing and prone to unpredictable weather. Iconic features like Eau Rouge make it a driver favourite.",
    "Hungarian Grand Prix": "The Hungaroring is tight and twisty — overtaking is hard and strategy often decides the race. It is sometimes called 'Monaco without the walls'.",
    "Dutch Grand Prix": "Zandvoort has sweeping banked corners and unique elevation, rewarding precision. Close walls make mistakes costly.",
    "Italian Grand Prix": "Monza is the 'Temple of Speed' with long straights and heavy braking zones. It favours low-drag setups and high top speed.",
    "Azerbaijan Grand Prix": "Baku combines absurdly long straights with tight castle corner sections, producing chaotic races. Expect strategy and street-circuit incidents.",
    "Singapore Grand Prix": "Marina Bay is a physically punishing night street race with high heat and humidity. Mistakes are punished by close walls and low grip.",
    "United States Grand Prix": "Often in Austin, the US GP mixes fast flowing corners and elevation changes with a great fan atmosphere. It’s a season highlight for many.",
    "Mexico City Grand Prix": "High altitude at Autódromo Hermanos Rodríguez affects downforce and engine behaviour. The stadium section is loud and visually striking.",
    "São Paulo Grand Prix": "Interlagos is historic and undulating with mixed-conditions race potential. It often delivers dramatic championship moments.",
    "Las Vegas Grand Prix": "Las Vegas is a bright, night-time street spectacle on the Strip with challenging kerbs and surface changes. The event is as much show as race.",
    "Qatar Grand Prix": "Losail is a fast, smooth circuit adapted from MotoGP with night running and desert wind factors. Track temperature and sand can influence tyre behaviour.",
    "Abu Dhabi Grand Prix": "Yas Marina is a twilight season finale that blends permanent and marina-side layout. It often hosts championship-deciding drama in calm conditions.",
    "Pre-Season Testing": "Being the first time we see the new cars hit the track, testing is filled with unknowns, speculation, and intrigue. Who will be the fastest of them all ?"
}