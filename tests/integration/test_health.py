def test_health_check_endpoint(client):
    """
    Test that the root health check endpoint is operational and returns correct payload.
    """
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["application"] == "LifeLink AI"
    assert data["status"] == "running"
