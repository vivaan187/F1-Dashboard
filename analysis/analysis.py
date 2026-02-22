import fastf1
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def TopSpeedVSAvgSpeed(Year: int, GrandPrix: str, Session: str):

    # -------------------------------
    # Load session
    # -------------------------------
    session = fastf1.get_session(Year, GrandPrix, Session)
    session.load()

    # Pick clean laps
    laps = session.laps.pick_quicklaps()
    teams = laps["Team"].unique()

    # For storing results
    avg_speeds = {}
    top_speeds = {}

    # 2025 team colours
    team_colors = {
        "Red Bull": "#0600EF",
        "Ferrari": "#DC0000",
        "Mercedes": "#00D2BE",
        "McLaren": "#FF8700",
        "Aston Martin": "#006F62",
        "Alpine": "#0090FF",
        "RB": "#6692FF",
        "Sauber": "#52E252",
        "Williams": "#00A0DE",
        "Haas": "#B6BABD"
    }

    # -------------------------------
    # Compute speeds
    # -------------------------------
    for team in teams:
        team_laps = laps[laps["Team"] == team]
        drivers = team_laps["Driver"].unique()

        lap_avg_speeds = []
        team_top_speed_list = []

        for drv in drivers:
            driver_laps = team_laps[team_laps["Driver"] == drv]

            for _, lap in driver_laps.iterrows():

                tel = lap.get_telemetry()
                if tel.empty:
                    continue

                speed = tel["Speed"].values              # km/h
                time = tel["Time"].values               # numpy.timedelta64 array

                # Convert timedelta64 → seconds
                t = time.view("timedelta64[ns]").astype(float) / 1e9

                if len(t) < 2:
                    continue

                dt = np.diff(t)
                v = speed[:-1]

                # Numerical integration: avg speed = ∫v dt / T
                avg_speed = np.sum(v * dt) / (t[-1] - t[0])
                lap_avg_speeds.append(avg_speed)

                # Top speed of lap
                team_top_speed_list.append(speed.max())

        # Store results
        avg_speeds[team] = np.mean(lap_avg_speeds) if lap_avg_speeds else np.nan
        top_speeds[team] = np.max(team_top_speed_list) if team_top_speed_list else np.nan

    # -------------------------------
    # Plot
    # -------------------------------
    fig, ax = plt.subplots(figsize=(11, 8))

    teams_sorted = sorted(avg_speeds.keys())

    for team in teams_sorted:
        x = avg_speeds[team]
        y = top_speeds[team]
        color = team_colors.get(team, "black")

        ax.scatter(x, y, s=250, color=color, edgecolor="black", linewidth=0.7)

        # Tight label placement
        ax.text(x + 0.05, y - 0.25, team,
                fontsize=6, weight="bold", color=color)

    # -------------------------------
    # Style: quadrant lines
    # -------------------------------
    mean_x = np.nanmean(list(avg_speeds.values()))
    mean_y = np.nanmean(list(top_speeds.values()))

    ax.axhline(mean_y, color="black", lw=1)
    ax.axvline(mean_x, color="black", lw=1)

    # Quadrant arrows
    ax.annotate("", xy=(mean_x+3, mean_y), xytext=(mean_x-3, mean_y),
                arrowprops=dict(arrowstyle="<->", lw=1.2))
    ax.text(mean_x+1.2, mean_y+0.2, "Quick", fontsize=10)
    ax.text(mean_x-1.2, mean_y+0.2, "Slow", fontsize=10)

    ax.annotate("", xy=(mean_x, mean_y+3), xytext=(mean_x, mean_y-3),
                arrowprops=dict(arrowstyle="<->", lw=1.2))
    ax.text(mean_x+0.2, mean_y+1.2, "Low Drag", fontsize=10, rotation=0)
    ax.text(mean_x+0.2, mean_y-1.2, "High Drag", fontsize=10, rotation=0)

    # -------------------------------
    # Labels & title
    # -------------------------------
    ax.set_xlabel("Mean Speed (km/h)", fontsize=13)
    ax.set_ylabel("Top Speed (km/h)", fontsize=13)
    ax.set_title(
        f"{Year} {GrandPrix} – {Session}\nTop Speed vs Mean Lap Speed",
        fontsize=15, weight="bold"
    )

    ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.show()

#TopSpeedVSAvgSpeed(2025,"Britain","Q")

def FullRacePaceAnalysis(
        year: int,
        grand_prix: str,
        driver_A: str,
        driver_B: str,
        fuel_load_start: float = 105.0,
        fuel_per_lap: float = 1.6,
        delta_per_kg: float = 0.035
    ):
    """
    Compares race pace between two drivers:
    - Dark mode
    - Tyre compound colours
    - Driver A: solid lines
    - Driver B: dotted lines
    - Raw laps = faint dots
    - Corrected laps = styled lines
    """

    plt.style.use("dark_background")

    compound_colors = {
        "SOFT": "#FF4D4D",
        "MEDIUM": "#FFD84D",
        "HARD": "#FFFFFF",
        "INTERMEDIATE": "#32CD32",
        "WET": "#1E90FF"
    }

    line_styles = {driver_A: "solid", driver_B: "dotted"}

    session = fastf1.get_session(year, grand_prix, "R")
    session.load()

    plt.figure(figsize=(15, 8))

    for driver in [driver_A, driver_B]:

        laps = session.laps.pick_driver(driver).pick_quicklaps()

        if laps.empty:
            print(f"No usable laps for driver {driver}, skipping.")
            continue

        lap_numbers = laps["LapNumber"].to_numpy()
        lap_times = laps["LapTime"].dt.total_seconds().to_numpy()
        compounds = laps["Compound"].fillna("UNKNOWN").to_numpy()

        fuel_remaining = np.clip(
            fuel_load_start - lap_numbers * fuel_per_lap, 0, None
        )
        fuel_correction = fuel_remaining * delta_per_kg
        corrected = lap_times - fuel_correction

        print(f"\n====== DRIVER {driver} ======")
        print(f"Avg raw pace:        {np.mean(lap_times):.3f}s")
        print(f"Avg corrected pace:  {np.mean(corrected):.3f}s")

        for comp in np.unique(compounds):

            mask = (compounds == comp)
            color = compound_colors.get(comp.upper(), "#AAAAAA")
            ls = line_styles[driver]

            # Get indices for this compound
            comp_laps = lap_numbers[mask]
            comp_times_raw = lap_times[mask]
            comp_times_corr = corrected[mask]

            # -------- SPLIT INTO STINTS --------
            # A new stint begins every time the lap number increases by >1
            stint_breaks = np.where(np.diff(comp_laps) > 1)[0] + 1
            stint_indices = np.split(np.arange(len(comp_laps)), stint_breaks)
            # -----------------------------------

            for stint in stint_indices:
                # Raw dots
                plt.scatter(
                    comp_laps[stint],
                    comp_times_raw[stint],
                    s=30,
                    color=color,
                    alpha=0.28,
                )

                # Corrected line (NO cross-stint straight lines)
                plt.plot(
                    comp_laps[stint],
                    comp_times_corr[stint],
                    linestyle=ls,
                    linewidth=2.1,
                    color=color,
                    label=f"{driver} – {comp}" if stint is stint_indices[0] else None
                )


        print(f"Per-compound corrected pace:")
        for comp in np.unique(compounds):
            mask = (compounds == comp)
            print(f"  {comp}: {np.mean(corrected[mask]):.3f}s")

    plt.title(
        f"Fuel-Corrected Race Pace Comparison — {driver_A} vs {driver_B}\n{year} {grand_prix}",
        fontsize=16,
        weight="bold"
    )
    plt.xlabel("Lap Number", fontsize=13)
    plt.ylabel("Lap Time (s)", fontsize=13)
    plt.grid(alpha=0.2)

    plt.legend(fontsize=9)
    plt.tight_layout()
    plt.show()

