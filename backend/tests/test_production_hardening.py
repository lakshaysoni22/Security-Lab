from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_reports_production_defaults():
    client = TestClient(app)
    response = client.get('/api/health')

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'healthy'
    assert payload['demo_data_enabled'] is False
    assert payload['background_tasks_enabled'] is False
