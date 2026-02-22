import fastf1
from flask import jsonify
import numpy as np

def DriverVSDriverQuali(year: int,gp: str,DriverA: str,DriverB: str):
    
    print("To be done")

def DriverTelemetryVisualised(year: int,gp: str,driver: str):
    session = fastf1.get_session(year, gp, "Q")
    session.load(telemetry=True)

    lap = session.laps.pick_drivers(driver).pick_fastest()
    tel = lap.get_telemetry()[['X', 'Y', 'Time', 'Speed', 'Throttle', 'Brake','nGear','RPM','DRS']].dropna()

    # Convert to seconds from lap start
    time_sec = tel['Time'].dt.total_seconds().to_numpy()
    x = tel['X'].to_numpy()
    y = tel['Y'].to_numpy()

    # Normalize time to start at 0
    time_sec = time_sec - time_sec[0]

    # ---- REMOVE DUPLICATE TIMESTAMPS ----
    unique_indices = np.unique(time_sec, return_index=True)[1]
    time_sec = time_sec[unique_indices]
    x = x[unique_indices]
    y = y[unique_indices]

    # Target 60Hz timeline
    total_time = time_sec[-1]
    new_time = np.arange(0, total_time, 1/60)

    # Interpolate cleanly
    new_x = np.interp(new_time, time_sec, x)
    new_y = np.interp(new_time, time_sec, y)
    speed = tel['Speed'].to_numpy()
    throttle = tel['Throttle'].to_numpy()
    brake = tel['Brake'].to_numpy()

    # Get auxillary data
    gear = tel['nGear'].to_numpy()
    rpm = tel['RPM'].to_numpy()
    drs = tel['DRS'].to_numpy()

    # Gear syncing
    indices = np.searchsorted(time_sec, new_time, side="right") - 1
    indices = np.clip(indices, 0, len(gear)-1)

    synced_gear = gear[indices]

    # Interpolate everything
    new_speed = np.interp(new_time, time_sec, speed)
    new_throttle = np.interp(new_time, time_sec, throttle)
    new_brake = np.interp(new_time, time_sec, brake)

    return jsonify({
        "x": new_x.tolist(),
        "y": new_y.tolist(),
        "t": new_time.tolist(),
        "speed": new_speed.tolist(),
        "throttle": new_throttle.tolist(),
        "brake": new_brake.tolist(),
        "gear": synced_gear.tolist(),
        "rpm": rpm.tolist(),
        "drs": drs.tolist(),
        "lap_time": float(total_time)
    })