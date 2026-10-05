import os
import sys
from pathlib import Path
import urllib.request
import json

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

base_url = 'http://localhost:8000'
endpoints = [
    ('/health', 'System Health & MongoDB Status'),
    ('/api/traffic/status', 'Pipeline Worker Status'),
    ('/api/traffic/runs', 'Database Runs History'),
    ('/api/analytics/macroscopic', 'Level 3 Macroscopic Analytics'),
    ('/api/spatial/network-geojson', 'Spatial Road Network GeoJSON'),
    ('/api/spatial/desire-lines-geojson', 'Spatial Desire Lines GeoJSON'),
    ('/api/spatial/queue-extents-geojson', 'Spatial Queue Extents GeoJSON'),
    ('/api/reasoning/congestion', 'Network Causal Reasoning (Alias)'),
    ('/api/reasoning/congestion-origin', 'Network Causal Reasoning (Origin)'),
    ('/api/reasoning/summary', 'Network Reasoning Summary'),
    ('/api/telemetry/tracks', 'Kinematic Telemetry Tracks'),
    ('/api/results', 'Full Dashboard Results Payload'),
    ('/api/traffic/results', 'Traffic Results Endpoint'),
]

print("=" * 85)
print("AERIX BACKEND END-TO-END VERIFICATION AUDIT")
print("=" * 85)

all_passed = True
for ep, name in endpoints:
    url = f"{base_url}{ep}"
    try:
        req = urllib.request.urlopen(url, timeout=5)
        status = req.status
        content = req.read().decode('utf-8')
        data = json.loads(content)
        size = len(content)
        print(f"[PASS] {status} OK | {name:<38} | {ep:<34} | {size:>7} bytes")
    except Exception as e:
        all_passed = False
        print(f"[FAIL] ERR   | {name:<38} | {ep:<34} | Error: {e}")

# MongoDB Direct Verification
try:
    from backend.core.database import mongo_manager
    mongo_ok = mongo_manager.connect()
    sync_db = mongo_manager.get_sync_db()
    db_name = sync_db.name if sync_db is not None else "None"
    collections = sync_db.list_collection_names() if sync_db is not None else []
    
    # Check document counts
    runs_count = sync_db["runs"].count_documents({}) if sync_db is not None else 0
    
    print("-" * 85)
    print(f"MongoDB Live Status: Connected={mongo_ok} | DB='{db_name}' | Collections={collections}")
    print(f"MongoDB Data Check:  Collection 'runs' has {runs_count} documents stored.")
except Exception as e:
    print(f"MongoDB verification error: {e}")

print("=" * 85)
if all_passed:
    print("ALL BACKEND ENDPOINTS AND SYSTEMS ARE FULLY OPERATIONAL END-TO-END!")
else:
    print("AUDIT FAILED ON ONE OR MORE ENDPOINTS.")
    sys.exit(1)
