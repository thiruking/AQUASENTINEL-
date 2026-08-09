def generate_recommendations(reading: dict, species: str, classification: str, contributions: list[dict]) -> list[str]:
    recs = []
    
    do = reading.get("dissolved_oxygen", 6.5)
    ammonia = reading.get("ammonia", 0.02)
    ph = reading.get("ph", 7.8)
    turbidity = reading.get("turbidity", 35.0)

    if do < 5.0:
        recs.append("LOW DISSOLVED OXYGEN: Activate mechanical aerators immediately & inspect stocking density.")
    if ammonia > 0.05:
        recs.append("HIGH AMMONIA: Reduce feed ration by 50%, perform 20% water exchange, and check organic sludge accumulation.")
    if ph < 7.5:
        recs.append("LOW pH: Apply agricultural lime (CaCO3) to buffer alkalinity and stabilize pH level.")
    elif ph > 8.8:
        recs.append("HIGH pH: Reduce active photosynthetic plankton bloom and apply fermented molasses.")
    if turbidity > 45.0:
        recs.append("HIGH TURBIDITY: Inspect inlet water source and evaluate pond sediment disturbance.")

    if not recs:
        recs.append("ALL PARAMETERS OPTIMAL: Maintain routine monitoring and standard feeding schedule.")

    return recs
