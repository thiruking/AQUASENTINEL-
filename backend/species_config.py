SPECIES_PROFILES = {
    "Shrimp": {
        "name": "Penaeus vannamei (Pacific White Shrimp)",
        "ph": {"min": 7.5, "max": 8.5, "weight": 1.2},
        "dissolved_oxygen": {"min": 5.0, "max": 9.0, "weight": 2.0},
        "ammonia": {"min": 0.0, "max": 0.1, "weight": 2.5},
        "nitrate": {"min": 0.0, "max": 20.0, "weight": 1.0},
        "turbidity": {"min": 25.0, "max": 45.0, "weight": 1.0},
        "temperature": {"min": 26.0, "max": 32.0, "weight": 1.1},
        "salinity": {"min": 10.0, "max": 30.0, "weight": 1.0}
    },
    "Tilapia": {
        "name": "Oreochromis niloticus (Nile Tilapia)",
        "ph": {"min": 6.5, "max": 9.0, "weight": 1.2},
        "dissolved_oxygen": {"min": 4.0, "max": 10.0, "weight": 2.0},
        "ammonia": {"min": 0.0, "max": 0.2, "weight": 2.5},
        "nitrate": {"min": 0.0, "max": 50.0, "weight": 1.0},
        "turbidity": {"min": 20.0, "max": 60.0, "weight": 0.8},
        "temperature": {"min": 24.0, "max": 32.0, "weight": 1.0},
        "salinity": {"min": 0.0, "max": 15.0, "weight": 0.8}
    },
    "Carp": {
        "name": "Cyprinus carpio (Common Carp)",
        "ph": {"min": 6.8, "max": 8.2, "weight": 1.2},
        "dissolved_oxygen": {"min": 5.0, "max": 9.5, "weight": 2.0},
        "ammonia": {"min": 0.0, "max": 0.05, "weight": 2.5},
        "nitrate": {"min": 0.0, "max": 30.0, "weight": 1.0},
        "turbidity": {"min": 15.0, "max": 40.0, "weight": 1.0},
        "temperature": {"min": 20.0, "max": 28.0, "weight": 1.1},
        "salinity": {"min": 0.0, "max": 5.0, "weight": 1.2}
    }
}

def get_species_profile(species_name: str) -> dict:
    return SPECIES_PROFILES.get(species_name, SPECIES_PROFILES["Shrimp"])
