import fastf1
import pandas as pd
import numpy as np
from plotly.offline import plot
import plotly.graph_objects as go


# -------------------- Constants --------------------

COMPOUND_COLORS = {
    "SOFT": "#FF4D4D",
    "MEDIUM": "#FFD84D",
    "HARD": "#FFFFFF",
    "INTERMEDIATE": "#32CD32",
    "WET": "#1E90FF"
}


# -------------------- Utilities --------------------

def _coerce_secs(td_series: pd.Series) -> pd.Series:
    """Timedelta -> seconds, safe numeric conversion"""
    s = pd.to_numeric(td_series.dt.total_seconds(), errors="coerce")
    return s.replace([np.inf, -np.inf], np.nan)


def fuel_correct_lap(
    laptime_s: float,
    lap_number: int,
    total_laps: int,
    fuel_effect_per_10kg: float = 0.30,
    fuel_per_lap_kg: float = 1.85
) -> float:
    fuel_remaining = (total_laps - lap_number) * fuel_per_lap_kg
    return laptime_s - (fuel_remaining / 10.0) * fuel_effect_per_10kg


# -------------------- Main Dashboard --------------------

def combined_plotly_race_dashboard(year: int, grand_prix: str) -> str:
    session = fastf1.get_session(year, grand_prix, "R")
    session.load(telemetry=False, weather=False)

    # ==================================================
    # 1) Position change chart
    # ==================================================

    pos_fig = go.Figure()

    try:
        try:
            driver_colors = fastf1.plotting.get_driver_color_mapping(session=session)
        except Exception:
            driver_colors = {}

        for drv in session.drivers:
            drv_laps = session.laps.pick_drivers(drv).copy(deep=True)
            if drv_laps.empty:
                continue

            abb = drv_laps["Driver"].iloc[0]

            drv_laps.loc[:, "LapTime_s"] = _coerce_secs(drv_laps["LapTime"])

            customdata = np.column_stack([
                drv_laps["Compound"].fillna(""),
                drv_laps["LapTime_s"].fillna("")
            ])

            pos_fig.add_trace(go.Scatter(
                x=drv_laps["LapNumber"],
                y=drv_laps["Position"],
                mode="lines+markers",
                name=abb,
                text=[abb] * len(drv_laps),
                customdata=customdata,
                line=dict(color=driver_colors.get(abb)),
                marker=dict(size=6),
                hovertemplate=(
                    "Driver: %{text}<br>"
                    "Lap: %{x}<br>"
                    "Position: %{y}<br>"
                    "Tyre: %{customdata[0]}<br>"
                    "Lap time: %{customdata[1]:.3f} s"
                    "<extra></extra>"
                )
            ))

        pos_fig.update_layout(
            title=f"{year} {grand_prix} — Race Positions",
            template="plotly_dark",
            height=420
        )
        pos_fig.update_yaxes(autorange="reversed", dtick=1, title="Position")
        pos_fig.update_xaxes(title="Lap")

    except Exception as e:
        pos_fig = go.Figure()
        pos_fig.update_layout(
            template="plotly_dark",
            title="Position data unavailable",
            annotations=[dict(text=str(e), x=0.5, y=0.5, showarrow=False)]
        )

    # ==================================================
    # 2) Lap time violins (top 10)
    # ==================================================

    lap_fig = go.Figure()

    try:
        top10 = session.drivers[:10]
        driver_laps = (
            session.laps
            .pick_drivers(top10)
            .pick_quicklaps()
            .copy(deep=True)
            .reset_index(drop=True)
        )

        driver_laps.loc[:, "LapTime_s"] = _coerce_secs(driver_laps["LapTime"])
        driver_laps = driver_laps.dropna(subset=["LapTime_s"])

        try:
            driver_colors = fastf1.plotting.get_driver_color_mapping(session=session)
        except Exception:
            driver_colors = {}

        for drv in driver_laps["Driver"].unique():
            d = driver_laps[driver_laps["Driver"] == drv]

            lap_fig.add_trace(go.Violin(
                x=[drv] * len(d),
                y=d["LapTime_s"],
                name=drv,
                box_visible=True,
                meanline_visible=True,
                points="all",
                line=dict(color=driver_colors.get(drv)),
                marker=dict(size=4),
                hovertemplate=(
                    f"{drv}<br>"
                    "Lap time: %{y:.3f} s"
                    "<extra></extra>"
                )
            ))

        lap_fig.update_layout(
            title=f"{year} {grand_prix} — Quick Lap Distributions",
            template="plotly_dark",
            height=520,
            yaxis_title="Lap Time (s)",
            xaxis_title="Driver"
        )

    except Exception as e:
        lap_fig = go.Figure()
        lap_fig.update_layout(
            template="plotly_dark",
            title="Lap time data unavailable",
            annotations=[dict(text=str(e), x=0.5, y=0.5, showarrow=False)]
        )

    # ==================================================
    # 3) Fuel-corrected team pace
    # ==================================================

    team_fig = go.Figure()

    try:
        laps = session.laps.pick_quicklaps().copy(deep=True)
        laps.loc[:, "LapTime_s"] = _coerce_secs(laps["LapTime"])
        laps = laps.dropna(subset=["LapTime_s"])

        total_laps = int(laps["LapNumber"].max())

        laps.loc[:, "CorrectedLap_s"] = [
            fuel_correct_lap(
                row.LapTime_s,
                int(row.LapNumber),
                total_laps
            )
            for row in laps.itertuples()
        ]

        team_order = (
            laps.groupby("Team")["CorrectedLap_s"]
            .median()
            .sort_values()
            .index
        )

        for team in team_order:
            t = laps[laps["Team"] == team]

            team_fig.add_trace(go.Box(
                y=t["CorrectedLap_s"],
                name=team,
                boxmean=True,
                marker=dict(
                    color=fastf1.plotting.get_team_color(team, session=session)
                ),
                hovertemplate=(
                    f"{team}<br>"
                    "Corrected lap: %{y:.3f} s"
                    "<extra></extra>"
                )
            ))

        team_fig.update_layout(
            title=f"{year} {grand_prix} — Fuel-Corrected Team Pace",
            template="plotly_dark",
            height=520,
            yaxis_title="Corrected Lap Time (s)"
        )

    except Exception as e:
        team_fig = go.Figure()
        team_fig.update_layout(
            template="plotly_dark",
            title="Team pace unavailable",
            annotations=[dict(text=str(e), x=0.5, y=0.5, showarrow=False)]
        )

    # ==================================================
    # Render HTML
    # ==================================================

    return f"""
    <div class="race-dashboard">
        {plot(pos_fig, output_type="div", include_plotlyjs="cdn")}
        {plot(lap_fig, output_type="div", include_plotlyjs=False)}
        {plot(team_fig, output_type="div", include_plotlyjs=False)}
    </div>
    """


# -------------------- Driver vs Driver --------------------

def driver_vs_driver_pace_plot(
        year: int,
        grand_prix: str,
        driver_A: str,
        driver_B: str,
        fuel_load_start: float = 105.0,
        fuel_per_lap: float = 1.6,
        delta_per_kg: float = 0.035
    ) -> dict:

    session = fastf1.get_session(year, grand_prix, "R")
    session.load()

    compound_colors = {
        "SOFT": "#FF4D4D",
        "MEDIUM": "#FFD84D",
        "HARD": "#FFFFFF",
        "INTERMEDIATE": "#32CD32",
        "WET": "#1E90FF"
    }

    line_styles = {driver_A: "solid", driver_B: "dot"}

    traces = []

    for driver in [driver_A, driver_B]:

        laps = session.laps.pick_driver(driver).pick_quicklaps()

        if laps.empty:
            continue

        lap_numbers = laps["LapNumber"].to_numpy()
        lap_times = laps["LapTime"].dt.total_seconds().to_numpy()
        compounds = laps["Compound"].fillna("UNKNOWN").to_numpy()

        fuel_remaining = np.clip(
            fuel_load_start - lap_numbers * fuel_per_lap, 0, None
        )

        fuel_correction = fuel_remaining * delta_per_kg
        corrected = lap_times - fuel_correction

        for comp in np.unique(compounds):

            mask = (compounds == comp)
            color = compound_colors.get(comp.upper(), "#AAAAAA")
            ls = line_styles[driver]

            comp_laps = lap_numbers[mask]
            comp_raw = lap_times[mask]
            comp_corr = corrected[mask]

            if len(comp_laps) == 0:
                continue

            stint_breaks = np.where(np.diff(comp_laps) > 1)[0] + 1
            stint_indices = np.split(np.arange(len(comp_laps)), stint_breaks)

            for stint in stint_indices:

                # Raw markers
                traces.append({
                    "x": comp_laps[stint].tolist(),
                    "y": comp_raw[stint].tolist(),
                    "mode": "markers",
                    "marker": {
                        "size": 6,
                        "color": color,
                        "opacity": 0.28
                    },
                    "name": f"{driver} raw",
                    "showlegend": False
                })

                # Corrected line
                traces.append({
                    "x": comp_laps[stint].tolist(),
                    "y": comp_corr[stint].tolist(),
                    "mode": "lines",
                    "line": {
                        "color": color,
                        "width": 2.2,
                        "dash": ls
                    },
                    "name": f"{driver} – {comp}"
                })

    return {
        "data": traces,
        "layout": {
            "template": "plotly_dark",
            "height": 600,
            "title": f"Fuel-Corrected Race Pace — {driver_A} vs {driver_B}<br>{year} {grand_prix}",
            "xaxis": {"title": "Lap Number"},
            "yaxis": {"title": "Lap Time (s)"},
            "legend": {"title": {"text": "Driver / Compound"}}
        }
    }

