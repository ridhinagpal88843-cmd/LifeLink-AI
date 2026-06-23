import pytest
from backend.agents.location_agent import LocationRoutingAgent


def test_distance_calculation():
    """
    Verify Haversine formula calculation outputs.
    Distance from Civic Center SF (37.7749, -122.4194)
    to Mercy General Hospital SF (37.7849, -122.4094) should be around 0.87 miles.
    """
    agent = LocationRoutingAgent()
    dist = agent.calculate_distance(37.7749, -122.4194, 37.7849, -122.4094)
    assert dist > 0.8
    assert dist < 1.0


def test_reverse_geocoding():
    """
    Verify reverse geocoding street address conversion.
    """
    agent = LocationRoutingAgent()
    result = agent.reverse_geocode(37.7749, -122.4194)
    assert "Market St" in result.address
    assert "San Francisco" in result.address


def test_calculate_routing():
    """
    Verify routing result ETA calculations.
    """
    agent = LocationRoutingAgent()
    result = agent.calculate_routing(
        from_lat=37.7749,
        from_lon=-122.4194,
        hospital_name="Mercy Hospital",
        hospital_lat=37.7849,
        hospital_lon=-122.4094,
        incident_id="test-incident"
    )
    
    assert result.destination_hospital_name == "Mercy Hospital"
    assert result.distance_miles > 0.0
    assert result.duration_minutes >= 2
    assert "maps.lifelink.ai/live/test-incident" in result.live_tracking_url
