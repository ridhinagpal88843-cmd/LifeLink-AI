def test_health_check_endpoint(client):
    """
    Test that the /health endpoint is operational.
    """
    response = client.get("/health")
    assert response.status_type == 200 or response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "LifeLink AI"
