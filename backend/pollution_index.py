from .species_config import get_species_profile

def calculate_pollution_index(reading: dict, species: str = "Shrimp") -> tuple[float, list[dict]]:
    """
    Pollution Index (PI) Convention:
      0.0   = OPTIMAL / SAFE (No pollution, perfect parameters)
      100.0 = CRITICAL / SEVERE RISK (Extreme parameter deviation)

    Formula:
      PI = sum( Weight_i * Stress_i ) / sum( Weight_i ) * 100
      Where Stress_i measures deviation from ideal center if optimal, or overflow distance if out of bounds.
    """
    profile = get_species_profile(species)
    total_weighted_stress = 0.0
    total_weight = 0.0
    raw_contributions = []

    for param, limits in profile.items():
        if param == "name":
            continue
        val = reading.get(param)
        if val is None:
            continue

        p_min = limits["min"]
        p_max = limits["max"]
        weight = limits["weight"]
        total_weight += weight

        center = (p_min + p_max) / 2.0
        half_span = max(0.1, (p_max - p_min) / 2.0)

        if p_min <= val <= p_max:
            # Optimal range: Stress ranges smoothly from 0.0 (exact center) up to 0.25 (near boundaries)
            stress = (abs(val - center) / half_span) * 0.25
            status = "Optimal"
        else:
            # Out of bounds: Stress increases proportionally with distance past limit
            if val < p_min:
                dist = p_min - val
            else:
                dist = val - p_max
            stress = 0.25 + min(1.75, dist / half_span)
            status = "Critical" if stress > 0.85 else "Warning"

        weighted_stress = stress * weight
        total_weighted_stress += weighted_stress

        raw_contributions.append({
            "parameter": param,
            "weighted_stress": weighted_stress,
            "status": status,
            "current_value": float(round(val, 3)),
            "ideal_range": f"{p_min} - {p_max}"
        })

    # Normalize PI score between 0.0 (Best) and 100.0 (Worst)
    raw_score = (total_weighted_stress / (total_weight * 1.5)) * 100.0 if total_weight > 0 else 0.0
    pollution_index = round(min(100.0, max(0.0, raw_score)), 1)

    # Compute proportional percentage contribution for each parameter (avoids flat 0% bug)
    for c in raw_contributions:
        c["contribution_percent"] = round((c["weighted_stress"] / total_weighted_stress * 100.0), 1) if total_weighted_stress > 0 else 0.0
        del c["weighted_stress"]

    raw_contributions.sort(key=lambda x: x["contribution_percent"], reverse=True)
    return pollution_index, raw_contributions

def validate_and_reconcile_status(pi_score: float, ml_prediction: str, confidence: float) -> tuple[str, float]:
    """
    Consistency Validation Function:
    Ensures Pollution Index score, ML prediction, and final Safe/Moderate/Critical badges are aligned.
    """
    if pi_score >= 60.0 or ml_prediction == "Critical":
        final_status = "CRITICAL"
        reconciled_conf = max(confidence, round(0.85 + (pi_score / 100.0) * 0.14, 2))
    elif pi_score >= 30.0 or ml_prediction == "Moderate":
        final_status = "MODERATE"
        reconciled_conf = max(confidence, 0.82)
    else:
        final_status = "SAFE"
        reconciled_conf = max(confidence, 0.90)

    return final_status, min(0.99, reconciled_conf)
