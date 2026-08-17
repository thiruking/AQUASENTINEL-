import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.pollution_index import calculate_pollution_index, validate_and_reconcile_status
from backend.classifier import classifier_instance

client = TestClient(app)

def test_pollution_index_optimal_convention():
    """
    Test BUG 2 Fix: Verify Pollution Index score is near 0.0 for optimal parameters
    and that relative parameter contributions are non-zero.
    """
    optimal_reading = {
        "ph": 7.8,
        "temperature": 28.0,
        "turbidity": 30.0,
        "dissolved_oxygen": 6.5,
        "ammonia": 0.02,
        "bod": 3.5,
        "co2": 4.0,
        "salinity": 15.0
    }

    score, contributions = calculate_pollution_index(optimal_reading, "Shrimp")

    # Optimal parameters should yield a low score (< 20/100)
    assert 0.0 <= score <= 20.0, f"Expected low score for optimal reading, got {score}"

    # Contributions should not be flat 0% for all parameters
    percentages = [c["contribution_percent"] for c in contributions]
    assert sum(percentages) > 0, "Parameter percentage contributions should sum to ~100%"
    assert any(p > 0 for p in percentages), "Parameters must show relative stress contribution"

def test_pollution_index_critical_convention():
    """
    Test that severe parameter deviations produce high Pollution Index scores (> 50/100).
    """
    critical_reading = {
        "ph": 5.5,
        "temperature": 36.0,
        "turbidity": 85.0,
        "dissolved_oxygen": 1.5,
        "ammonia": 0.50,
        "bod": 15.0,
        "co2": 25.0,
        "salinity": 2.0
    }

    score, contributions = calculate_pollution_index(critical_reading, "Shrimp")
    assert score >= 50.0, f"Expected high score for critical reading, got {score}"

def test_status_reconciliation_consistency():
    """
    Test consistency validation function.
    """
    status, conf = validate_and_reconcile_status(65.0, "Critical", 0.95)
    assert status == "CRITICAL"
    assert conf >= 0.85

    status_safe, conf_safe = validate_and_reconcile_status(10.0, "Safe", 0.92)
    assert status_safe == "SAFE"

def test_classifier_prediction():
    """
    Test ML classifier output structure.
    """
    sample = {
        "ph": 7.8,
        "temperature": 28.0,
        "turbidity": 30.0,
        "dissolved_oxygen": 6.5,
        "ammonia": 0.02,
        "salinity": 15.0
    }
    label, conf, shap_scores = classifier_instance.predict(sample)
    assert label in ["Safe", "Moderate", "Critical"]
    assert 0.0 <= conf <= 1.0
    assert len(shap_scores) > 0

def test_api_health_endpoint():
    """
    Test /api/health endpoint.
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "dataset_samples" in data

def test_api_predict_endpoint():
    """
    Test /api/predict endpoint.
    """
    payload = {
        "species": "Shrimp",
        "temperature": 28.5,
        "turbidity": 35.0,
        "DO": 6.5,
        "ph": 7.8,
        "ammonia": 0.02,
        "salinity": 15.0
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "pollution_index" in data
    assert "final_classification" in data
    assert "parameter_contributions" in data

def test_extreme_reading_is_critical():
    """Dangerous slider values must never be reported as SAFE."""
    payload = {
        "species": "Shrimp",
        "temperature": 40.0,
        "turbidity": 99.0,
        "DO": 12.0,
        "ph": 10.0,
        "ammonia": 0.5,
        "nitrate": 100.0,
        "salinity": 44.5,
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["pollution_index"] >= 60.0
    assert data["final_classification"] == "CRITICAL"
    assert data["recommendations"]


def test_api_metrics_endpoint():
    """
    Test /api/model/metrics endpoint.
    """
    response = client.get("/api/model/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert len(metrics) >= 5
    assert any(m["is_best"] for m in metrics)


def test_report_downloads_are_valid_files():
    """CSV and PDF report endpoints must send actual downloadable file data."""
    csv_response = client.get("/api/report")
    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")
    assert "attachment;" in csv_response.headers["content-disposition"]
    assert csv_response.content.startswith(b"timestamp,species,")

    pdf_response = client.get("/api/report/pdf")
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert "attachment;" in pdf_response.headers["content-disposition"]
    assert pdf_response.content.startswith(b"%PDF-")
    assert len(pdf_response.content) > 500

def test_user_registration_and_login():
    """
    Test JWT Authentication: Register, Login, and Auth Token validation.
    """
    import time
    test_email = f"farmer_{int(time.time())}@aquasentinel.demo"
    reg_payload = {
        "name": "Test Farmer",
        "email": test_email,
        "password": "farmerpass123",
        "farm_name": "Sunrise Aquaculture"
    }
    # Register
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 200

    # Login
    login_payload = {
        "email": test_email,
        "password": "farmerpass123"
    }
    login_res = client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    token = data["access_token"]

    # Verify /api/auth/me
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["email"] == test_email


def test_user_pond_creation():
    """
    Test User Custom Pond Creation API.
    """
    login_res = client.post("/api/auth/login", json={"email": "admin@aquasentinel.demo", "password": "demo1234"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    pond_payload = {"name": "Test Pond Delta", "species": "Tilapia"}
    res = client.post("/api/ponds/create", json=pond_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Test Pond Delta"
    assert data["species"] == "Tilapia"

