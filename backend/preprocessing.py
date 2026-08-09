import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

try:
    from imblearn.over_sampling import SMOTE
    HAS_SMOTE = True
except ImportError:
    HAS_SMOTE = False

# STRICT RULE: Raw physical parameters ONLY. NO target-derived columns (like Pollution Index).
FEATURE_COLS = [
    "temperature", "turbidity", "dissolved_oxygen", "bod", "co2", "ph",
    "alkalinity", "hardness", "calcium", "ammonia", "nitrite", "phosphorus",
    "h2s", "plankton", "nitrate", "salinity"
]

LABEL_MAP = {"Safe": 0, "Moderate": 1, "Critical": 2}
REVERSE_LABEL_MAP = {0: "Safe", 1: "Moderate", 2: "Critical"}

def preprocess_and_split(df: pd.DataFrame):
    # 1. Deduplicate dataset to prevent data leakage across split
    df_clean = df.drop_duplicates().copy()

    X = df_clean[FEATURE_COLS].copy()
    y = df_clean["status"].map(LABEL_MAP)

    # Impute missing values if any
    X = X.fillna(X.median())

    # 2. Stratified Train/Test Split (80/20) - PERFORMED BEFORE ANY SCALING OR SMOTE FITTING
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 3. Fit SMOTE ONLY on training fold (Prevents test-set contamination)
    if HAS_SMOTE:
        smote = SMOTE(random_state=42)
        X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
    else:
        X_train_res, y_train_res = X_train, y_train

    # 4. Fit StandardScaler ONLY on training fold
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_res)
    X_test_scaled = scaler.transform(X_test)

    return X_train_scaled, X_test_scaled, y_train_res, y_test, scaler
