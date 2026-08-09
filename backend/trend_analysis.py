import numpy as np

def analyze_trend(recent_readings: list[dict], target_param: str = "ammonia") -> tuple[bool, str]:
    """
    Analyzes historical readings to detect gradual water quality deterioration
    before hard threshold breaches occur.
    """
    if not recent_readings or len(recent_readings) < 3:
        return False, "Insufficient history for trend detection."

    values = [r.get(target_param, 0.0) for r in recent_readings if r.get(target_param) is not None]
    if len(values) < 3:
        return False, "Insufficient parameter history."

    x = np.arange(len(values))
    slope, _ = np.polyfit(x, values, 1)

    if target_param in ["ammonia", "nitrite", "turbidity", "temperature"] and slope > 0.02:
        return True, f"Gradual deterioration detected: {target_param} rising at +{round(slope, 4)} per step."
    elif target_param in ["dissolved_oxygen", "ph"] and slope < -0.05:
        return True, f"Gradual deterioration detected: {target_param} dropping at {round(slope, 4)} per step."

    return False, "Parameters stable over recent timeframe."
