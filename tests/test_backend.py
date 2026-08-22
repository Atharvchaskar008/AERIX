"""
AERIX Backend API Integration Test Suite
Validates all 5 competition criteria endpoints with FastAPI and MongoDB.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["system"] == "AERIX Aerial Traffic Platform"


def test_traffic_status(client):
    response = client.get("/api/traffic/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "progress" in data


def test_traffic_runs_list(client):
    response = client.get("/api/traffic/runs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_macroscopic_analytics(client):
    response = client.get("/api/analytics/macroscopic")
    assert response.status_code == 200
    data = response.json()
    assert "turning_movements" in data
    assert "speed_profiles" in data
    assert "lane_analytics" in data


def test_spatial_network_geojson(client):
    response = client.get("/api/spatial/network-geojson")
    assert response.status_code == 200
    data = response.json()
    assert data.get("type") == "FeatureCollection"
    assert len(data.get("features", [])) > 0


def test_spatial_desire_lines_geojson(client):
    response = client.get("/api/spatial/desire-lines-geojson")
    assert response.status_code == 200
    data = response.json()
    assert data.get("type") == "FeatureCollection"


def test_spatial_queue_extents_geojson(client):
    response = client.get("/api/spatial/queue-extents-geojson")
    assert response.status_code == 200
    data = response.json()
    assert data.get("type") == "FeatureCollection"


def test_network_reasoning_congestion(client):
    response = client.get("/api/reasoning/congestion-origin")
    assert response.status_code == 200
    data = response.json()
    assert "jam_detected" in data or "is_jam_active" in data or "bottleneck_link" in data


def test_telemetry_tracks_and_summary(client):
    summary_resp = client.get("/api/telemetry/summary")
    assert summary_resp.status_code == 200
    assert "unique_tracks" in summary_resp.json()

    tracks_resp = client.get("/api/telemetry/tracks")
    assert tracks_resp.status_code == 200
    assert isinstance(tracks_resp.json(), list)
