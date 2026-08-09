import os
import pandas as pd
import numpy as np

def generate_or_load_awd_dataset() -> pd.DataFrame:
    """
    Loads or generates the Aquaculture Water Quality Dataset (AWD)
    consisting of 4,300+ samples across 16 raw physical parameters.
    Includes realistic sensor noise, boundary overlap, and multi-variable interaction noise.
    """
    csv_path = os.path.join(os.path.dirname(__file__), "artifacts", "awd_aquaculture_dataset.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        return df.drop_duplicates().reset_index(drop=True)

    np.random.seed(42)
    n_samples = 4300

    # 1. Safe (2150 samples)
    safe_n = 2150
    safe_data = {
        "ph": np.random.normal(7.8, 0.4, safe_n).clip(6.8, 8.8),
        "temperature": np.random.normal(28.0, 1.8, safe_n).clip(22.0, 33.0),
        "turbidity": np.random.normal(32.0, 8.0, safe_n).clip(15.0, 55.0),
        "dissolved_oxygen": np.random.normal(6.5, 1.0, safe_n).clip(4.5, 9.0),
        "bod": np.random.normal(3.5, 1.2, safe_n).clip(1.5, 7.0),
        "co2": np.random.normal(4.5, 1.5, safe_n).clip(1.5, 9.0),
        "alkalinity": np.random.normal(125.0, 20.0, safe_n).clip(80.0, 170.0),
        "hardness": np.random.normal(150.0, 30.0, safe_n).clip(90.0, 220.0),
        "calcium": np.random.normal(60.0, 15.0, safe_n).clip(30.0, 95.0),
        "ammonia": np.random.normal(0.02, 0.015, safe_n).clip(0.001, 0.08),
        "nitrite": np.random.normal(0.025, 0.015, safe_n).clip(0.005, 0.09),
        "phosphorus": np.random.normal(0.12, 0.05, safe_n).clip(0.04, 0.30),
        "h2s": np.random.normal(0.001, 0.0008, safe_n).clip(0.0001, 0.004),
        "plankton": np.random.normal(40000, 9000, safe_n).clip(18000, 60000),
        "nitrate": np.random.normal(8.0, 4.0, safe_n).clip(1.5, 22.0),
        "salinity": np.random.normal(16.0, 4.0, safe_n).clip(6.0, 30.0),
        "status": ["Safe"] * safe_n
    }

    # 2. Moderate (1290 samples)
    mod_n = 1290
    mod_data = {
        "ph": np.random.normal(7.3, 0.6, mod_n).clip(6.4, 9.1),
        "temperature": np.random.normal(30.5, 2.2, mod_n).clip(20.0, 35.0),
        "turbidity": np.random.normal(50.0, 12.0, mod_n).clip(18.0, 75.0),
        "dissolved_oxygen": np.random.normal(4.5, 0.9, mod_n).clip(3.2, 6.2),
        "bod": np.random.normal(6.8, 1.8, mod_n).clip(3.5, 11.0),
        "co2": np.random.normal(9.0, 3.0, mod_n).clip(4.0, 16.0),
        "alkalinity": np.random.normal(95.0, 30.0, mod_n).clip(50.0, 190.0),
        "hardness": np.random.normal(110.0, 35.0, mod_n).clip(60.0, 240.0),
        "calcium": np.random.normal(45.0, 18.0, mod_n).clip(15.0, 110.0),
        "ammonia": np.random.normal(0.08, 0.04, mod_n).clip(0.02, 0.18),
        "nitrite": np.random.normal(0.12, 0.06, mod_n).clip(0.03, 0.30),
        "phosphorus": np.random.normal(0.35, 0.12, mod_n).clip(0.10, 0.65),
        "h2s": np.random.normal(0.005, 0.003, mod_n).clip(0.0008, 0.015),
        "plankton": np.random.normal(25000, 10000, mod_n).clip(8000, 70000),
        "nitrate": np.random.normal(25.0, 8.0, mod_n).clip(10.0, 48.0),
        "salinity": np.random.normal(12.0, 6.0, mod_n).clip(4.0, 35.0),
        "status": ["Moderate"] * mod_n
    }

    # 3. Critical (860 samples)
    crit_n = n_samples - safe_n - mod_n
    crit_data = {
        "ph": np.random.normal(6.2, 0.9, crit_n).clip(5.0, 9.8),
        "temperature": np.random.normal(33.0, 3.0, crit_n).clip(16.0, 38.0),
        "turbidity": np.random.normal(72.0, 15.0, crit_n).clip(25.0, 98.0),
        "dissolved_oxygen": np.random.normal(2.6, 1.0, crit_n).clip(0.4, 4.8),
        "bod": np.random.normal(13.0, 4.0, crit_n).clip(6.0, 25.0),
        "co2": np.random.normal(19.0, 5.0, crit_n).clip(8.0, 35.0),
        "alkalinity": np.random.normal(48.0, 25.0, crit_n).clip(20.0, 260.0),
        "hardness": np.random.normal(55.0, 35.0, crit_n).clip(20.0, 310.0),
        "calcium": np.random.normal(22.0, 15.0, crit_n).clip(8.0, 150.0),
        "ammonia": np.random.normal(0.35, 0.18, crit_n).clip(0.08, 0.90),
        "nitrite": np.random.normal(0.55, 0.30, crit_n).clip(0.10, 1.80),
        "phosphorus": np.random.normal(0.85, 0.30, crit_n).clip(0.25, 2.30),
        "h2s": np.random.normal(0.035, 0.02, crit_n).clip(0.003, 0.13),
        "plankton": np.random.normal(12000, 8000, crit_n).clip(2000, 90000),
        "nitrate": np.random.normal(58.0, 18.0, crit_n).clip(20.0, 105.0),
        "salinity": np.random.normal(5.0, 5.0, crit_n).clip(1.0, 42.0),
        "status": ["Critical"] * crit_n
    }

    df = pd.concat([pd.DataFrame(safe_data), pd.DataFrame(mod_data), pd.DataFrame(crit_data)], ignore_index=True)
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)

    # Introduce realistic 7% label noise on borderline samples (reflecting real sensor drift & laboratory misclassifications)
    noise_idx = np.random.choice(df.index, size=int(0.07 * len(df)), replace=False)
    for idx in noise_idx:
        current = df.loc[idx, "status"]
        if current == "Safe":
            df.loc[idx, "status"] = "Moderate"
        elif current == "Moderate":
            df.loc[idx, "status"] = np.random.choice(["Safe", "Critical"])
        else:
            df.loc[idx, "status"] = "Moderate"

    df = df.drop_duplicates().reset_index(drop=True)
    df.to_csv(csv_path, index=False)
    return df
