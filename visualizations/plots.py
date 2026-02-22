import fastf1
import fastf1.plotting
import matplotlib
matplotlib.use("Agg") # Ensures that no MatPlotLib GUI's are enabled 
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import numpy as np
import os

# Enabling cache
fastf1.Cache.enable_cache("C:/Users/vivaa/F1/f1_dashboard/cache")

# Setting up dark theme
fastf1.plotting.setup_mpl(misc_mpl_mods=False, color_scheme='fastf1')

# Drivers and Tracks list
drivers_list = ["LEC","HAM","NOR","PIA","VER","TSU","RUS","ANT","ALO","STR","SAI","ALB","HUL","BOR","LAW","HAD","OCO","BEA","GAS","COL"]
tracks = ["Australia","China","Japan","Bahrain","Saudi Arabia","Miami","Emilia Romagna","Monaco","Spain","Canada","Austria","Britian","Belgium","Hungary","Netherlands","Italy","Baku","Singapore","United States","Mexico City","Sao Paulo","Las Vegas","Qatar","Abu Dhabi"]

def SpeedAcrossQualiLap (Year : int,GrandPrix : str,Driver : str):

    # Load session
    session = fastf1.get_session(Year, GrandPrix, 'Q')
    session.load()

    # Get fastest lap speed over time
    fast_driver = session.laps.pick_drivers(Driver).pick_fastest()
    driver_car_data = fast_driver.get_car_data()
    t = driver_car_data['Time']
    vCar = driver_car_data['Speed']

    # Plot graph
    fig, ax = plt.subplots()
    ax.plot(t, vCar, label='Fast')
    ax.set_xlabel('Time')
    ax.set_ylabel('Speed [Km/h]')
    ax.set_title(f'{Driver} Fastest Lap')
    ax.legend()
    
    # Save 
    buf = BytesIO()
    # plt.show() # Optional 
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def RacePOSChange (Year : int,GrandPrix : str): 

    # Load session
    session = fastf1.get_session(Year,GrandPrix, 'R')
    session.load(telemetry=False, weather=False)

    # Create sub plots
    fig, ax = plt.subplots(figsize=(9.5, 5))

    # Get drivers' positions over the laps
    for drv in session.drivers:
        drv_laps = session.laps.pick_drivers(drv)

        abb = drv_laps['Driver'].iloc[0]
        style = fastf1.plotting.get_driver_style(identifier=abb,style=['color', 'linestyle'],session=session)

        ax.plot(drv_laps['LapNumber'], drv_laps['Position'],label=abb, **style)

    # Plot graph
    ax.set_ylim([20.5, 0.5])
    ax.set_yticks([1, 5, 10, 15, 20])
    ax.set_xlabel('Lap')
    ax.set_ylabel('Position')

    ax.legend(bbox_to_anchor=(1.0, 1.02))

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def RaceLapTimePlot (Year : int,GrandPrix : str):

    # Load session
    race = fastf1.get_session(Year, GrandPrix, 'R')
    race.load()

    # Get data for point finishers only
    point_finishers = race.drivers[:10]
    # print(point_finishers)
    driver_laps = race.laps.pick_drivers(point_finishers).pick_quicklaps()
    driver_laps = driver_laps.reset_index()

    finishing_order = [race.get_driver(i)["Abbreviation"] for i in point_finishers]
    # print(finishing_order)

    # Create the figure
    fig, ax = plt.subplots(figsize=(10, 5))

    # Seaborn doesn't have proper timedelta support,
    # Convert timedelta to float (in seconds)
    driver_laps["LapTime(s)"] = driver_laps["LapTime"].dt.total_seconds()

    sns.violinplot(data=driver_laps,
                x="Driver",
                y="LapTime(s)",
                hue="Driver",
                inner=None,
                density_norm="area",
                order=finishing_order,
                palette=fastf1.plotting.get_driver_color_mapping(session=race)
                )

    sns.swarmplot(data=driver_laps,
                x="Driver",
                y="LapTime(s)",
                order=finishing_order,
                hue="Compound",
                palette=fastf1.plotting.get_compound_mapping(session=race),
                linewidth=0,
                size=4
                )
    
    # Plot graph 
    ax.set_xlabel("Driver")
    ax.set_ylabel("Lap Time (s)")
    plt.suptitle(f"{Year} {GrandPrix.upper()} Lap Time Distributions")
    sns.despine(left=True, bottom=True)

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def TeamPaceComp (Year : int,GrandPrix: str):

    # Load session
    race = fastf1.get_session(Year,GrandPrix,"R")
    race.load()
    laps = race.laps.pick_quicklaps()

    # Transform laptimes into total seconds
    transformed_laps = laps.copy()
    transformed_laps.loc[:, "LapTime (s)"] = laps["LapTime"].dt.total_seconds()

    # Order the team from the fastest (lowest median lap time) to slowest
    team_order = (
        transformed_laps[["Team", "LapTime (s)"]]
        .groupby("Team")
        .median()["LapTime (s)"]
        .sort_values()
        .index
    )
    # print(team_order)

    # Make a color palette associating team names to their respective HEX codes
    team_palette = {team: fastf1.plotting.get_team_color(team, session=race)
                    for team in team_order}
    
    # Plot graph
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(
        data=transformed_laps,
        x="Team",
        y="LapTime (s)",
        hue="Team",
        order=team_order,
        palette=team_palette,
        whiskerprops=dict(color="white"),
        boxprops=dict(edgecolor="white"),
        medianprops=dict(color="grey"),
        capprops=dict(color="white"),
    )
    
    plt.title(f"{Year} {GrandPrix.upper()} Grand Prix ")
    plt.grid(visible=False)

    # x-label is redundant
    ax.set(xlabel=None)
    
    buf = BytesIO()
    #plt.show # Optional
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def BrakePressure (Year : int,GrandPrix : str,Session : str,Driver: str):

    # Load session
    session = fastf1.get_session(Year,GrandPrix,Session)
    session.load()

    # Get brake telemetry for the chosen driver
    driver_lap = session.laps.pick_drivers(Driver).pick_fastest()
    driver_lap_data = driver_lap.get_car_data()
    time = driver_lap_data["Time"]
    brake_press = driver_lap_data["Brake"]

    # Plot graph
    fig, ax = plt.subplots()
    ax.plot(time, brake_press, label='Brake Pressure')
    ax.set_xlabel('Time')
    ax.set_ylabel('Brake Pressure')
    ax.set_title(f'{Driver} Brake Pressure Across Lap')
    ax.legend()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def ThrottleVSBrakePressure(Year : int, GrandPrix : str, Session : str, Driver : str):

    # Load session
    session = fastf1.get_session(Year, GrandPrix, Session)
    session.load()

    # Get telemetry for the chosen driver
    driver_lap = session.laps.pick_drivers(Driver).pick_fastest()
    car_data = driver_lap.get_car_data()

    time = car_data["Time"]
    speed = car_data["Speed"]
    throttle = car_data["Throttle"]
    brake = car_data["Brake"]

    # Normalize brake if it's 0 or 1
    if brake.max() <= 1.1:
        brake *= 100

    # Create stacked subplots
    fig, axs = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    axs[0].plot(time, throttle, color='green')
    axs[0].set_ylabel("Throttle (%)")
    axs[0].set_ylim(0, 105)
    axs[0].set_title(f'{Driver} - Throttle')

    axs[1].plot(time, brake, color='red')
    axs[1].set_ylabel("Brake (%)")
    axs[1].set_ylim(0, 105)
    axs[1].set_title(f'{Driver} - Brake Pressure')

    axs[2].plot(time, speed, color='blue')
    axs[2].set_ylabel("Speed (km/h)")
    axs[2].set_title(f'{Driver} - Speed')
    axs[2].set_xlabel("Time")

    for ax in axs:
        ax.grid(True)

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def DriverVSDriverStats (Year : int, GrandPrix : str, Session : str , Driver1 : str, Driver2 : str):

    # Load session
    session = fastf1.get_session(Year,GrandPrix,Session)
    session.load()

    # Get telemetry for chosen driver 1
    driver1_lap = session.laps.pick_drivers(Driver1).pick_fastest()
    driver1_lap_data = driver1_lap.get_car_data()

    time1 = driver1_lap_data["Time"]
    speed1 = driver1_lap_data["Speed"]
    throttle1 = driver1_lap_data["Throttle"]
    brake1 = driver1_lap_data["Brake"] * 100

    # Get driver 1 colour
    colour1 = fastf1.plotting.get_driver_color(Driver1,session)

    # Get telemetry for chosen driver 2
    driver2_lap = session.laps.pick_drivers(Driver2).pick_fastest()
    driver2_lap_data = driver2_lap.get_car_data()

    time2 = driver2_lap_data["Time"]
    speed2 = driver2_lap_data["Speed"]
    throttle2 = driver2_lap_data["Throttle"]
    brake2 = driver2_lap_data["Brake"] * 100

    # Get driver 2 colour
    colour2 = fastf1.plotting.get_driver_color(Driver2,session)

    fig, axs = plt.subplots(3,1,figsize = (12,8),sharex = True)

    # Create stacked subplots, with the telemetry of both drivers on on the same graphs
    axs[0].plot(time1,speed1,color = colour1)
    axs[0].plot(time2,speed2,color = colour2)
    axs[0].set_ylabel("Speed (km/h)")
    axs[0].set_title(f"{Driver1} vs {Driver2} - Speed")
    
    axs[1].plot(time1,throttle1,color = colour1)
    axs[1].plot(time2,throttle2,color = colour2)
    axs[1].set_ylabel("Throttle (%)")
    axs[1].set_title(f"{Driver1} vs {Driver2} - Throttle")

    axs[2].plot(time1,brake1,color = colour1)
    axs[2].plot(time2,brake2,color = colour2)
    axs[2].set_ylabel("Brake (%)")
    axs[2].set_title(f"{Driver1} vs {Driver2} - Brake Pressure")
    axs[2].set_xlabel("Time")

    for ax in axs:
        ax.grid(True)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def TyreStrategies (Year, GrandPrix):

    # Load session
    race = fastf1.get_session(Year,GrandPrix,"R")
    race.load()
    laps = race.laps

    # Get driver abbreviations 
    drivers = race.drivers
    # print(drivers)

    drivers = [race.get_driver(driver)["Abbreviation"] for driver in drivers]
    # print(drivers)

    # Grouping stints by different factors
    stints = laps[["Driver", "Stint", "Compound", "LapNumber"]]
    stints = stints.groupby(["Driver", "Stint", "Compound"])
    stints = stints.count().reset_index()

    stints = stints.rename(columns={"LapNumber": "StintLength"})
    # print(stints)

    # Plot graph
    fig, ax = plt.subplots(figsize=(10.8, 10))

    for driver in drivers:
        driver_stints = stints.loc[stints["Driver"] == driver]

        previous_stint_end = 0
        for idx, row in driver_stints.iterrows():
            # Each row contains the compound name and stint length
            # We can use this information to draw horizontal bars
            compound_color = fastf1.plotting.get_compound_color(row["Compound"],
                                                                session=race)
            plt.barh(
                y=driver,
                width=row["StintLength"],
                left=previous_stint_end,
                color=compound_color,
                edgecolor="black",
                fill=True
            )

            previous_stint_end += row["StintLength"]
    
    plt.title(f"{Year} {GrandPrix} Grand Prix Strategies")
    plt.xlabel("Lap Number")
    plt.grid(False)
    # Invert the y-axis so drivers that finish higher are closer to the top
    ax.invert_yaxis()

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)   
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

    
def DriverLapTimes (Year : int,GrandPrix : str,Session : str, *Drivers):
    # Load chosen session
    session = fastf1.get_session(Year,GrandPrix,Session)
    session.load()

    fig, ax = plt.subplots(figsize=(8,5))

    # Load laps for chosen drivers 
    for drivers in Drivers:
        laps = session.laps.pick_drivers(drivers).pick_quicklaps().reset_index()
        # Get driver styles
        style = fastf1.plotting.get_driver_style(drivers,style=['color','linestyle'],session=session)
        # Plot graphs
        ax.plot(laps['LapTime'], **style, label = drivers)

    # Set labels
    ax.set_xlabel("Lap Number")
    ax.set_ylabel("Lap Time")

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def DriverReactionTimes (Year: int,GrandPrix: str,Drivers):
    race = fastf1.get_session(Year,GrandPrix,"R")
    race.load()

    reaction_times = []
    
    start_lap = race.laps.pick_drivers(Drivers).pick_laps(1)
    telemetry = start_lap.get_car_data()
    time = telemetry["Time"]
    speed = telemetry["Speed"]

    t0 = time.iloc[0]

    t100 = time[speed >= 100].iloc[0] - t0
    t200 = time[speed >= 200].iloc[0] - t0

    reaction_times.append(t100)
    
    print(reaction_times)

def TrackDisplay():

    # path to static folder (outside visualizations)
    static_path = os.path.join(os.path.dirname(__file__), "..", "static")
    os.makedirs(static_path, exist_ok=True)

    saved_files = []  # keep track of saved image filenames

    for track_name in tracks:
        plt.figure(figsize=(6, 6))  # new figure for each track

        race = fastf1.get_session(2024, track_name, "R")
        race.load()

        lap = race.laps.pick_fastest()
        pos = lap.get_pos_data()
        track_info = race.get_circuit_info()

        def rotate(xy, *, angle):
            rot_mat = np.array([[np.cos(angle), np.sin(angle)],
                               [-np.sin(angle), np.cos(angle)]])
            return np.matmul(xy, rot_mat)

        track = pos.loc[:, ('X', 'Y')].to_numpy()
        track_angle = track_info.rotation / 180 * np.pi
        rotated_track = rotate(track, angle=track_angle)
        plt.plot(rotated_track[:, 0], rotated_track[:, 1])

        offset_vector = [1000, 0]  

        for _, corner in track_info.corners.iterrows():
            txt = f"{corner['Number']}{corner['Letter']}"
            offset_angle = corner['Angle'] / 180 * np.pi
            offset_x, offset_y = rotate(offset_vector, angle=offset_angle)
            text_x = corner['X'] + offset_x 
            text_y = corner['Y'] + offset_y 
            text_x, text_y = rotate([text_x, text_y], angle=track_angle)
            track_x, track_y = rotate([corner['X'], corner['Y']], angle=track_angle)

            plt.scatter(text_x, text_y, color='grey', s=300)
            plt.plot([track_x, text_x], [track_y, text_y], color='grey')
            plt.text(text_x, text_y, txt, va='center_baseline', ha='center', size='small', color='white')

        plt.title(race.event['Location'])
        plt.xticks([])
        plt.yticks([])
        plt.axis('equal')

        # save into ../static
        filename = f"{track_name.lower()}_track.png"
        filepath = os.path.join(static_path, filename)

        plt.savefig(filepath, bbox_inches="tight", dpi=150)
        plt.close()
        saved_files.append(filename)

        print(f"Saved {filepath}")

    return saved_files