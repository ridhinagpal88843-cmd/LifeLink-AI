import math
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.mcp.client import MCPClientRegistry

logger = logging.getLogger(__name__)


class ReverseGeocodeResult(BaseModel):
    address: str = Field(..., description="Human-readable address corresponding to GPS coordinates")
    latitude: float
    longitude: float


class RoutingResult(BaseModel):
    distance_miles: float = Field(..., description="Calculated distance to destination")
    duration_minutes: int = Field(..., description="Estimated travel duration in minutes")
    destination_hospital_name: str = Field(..., description="Name of the targeted medical facility")
    live_tracking_url: str = Field(..., description="Link to stream real-time coordinate tracking")


class LocationRoutingAgent:
    """
    Agent responsible for geocoding patient coordinates, tracking live position updates,
    and calculating routing parameters, integrating with the Maps MCP tool.
    """

    def __init__(self, mcp_client: Optional[MCPClientRegistry] = None):
        self.mcp_client = mcp_client

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculates the distance in miles using the Haversine formula.
        """
        r = 3958.8
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_phi / 2.0) ** 2 +
             math.cos(phi1) * math.cos(phi2) *
             math.sin(delta_lambda / 2.0) ** 2)
        
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    def reverse_geocode(self, latitude: float, longitude: float) -> ReverseGeocodeResult:
        """
        Converts latitude and longitude into street address via Maps MCP geocode tool.
        """
        if self.mcp_client:
            res = self.mcp_client.maps_geocode(latitude, longitude)
            return ReverseGeocodeResult(
                address=res.get("formatted_address", "Unknown Address"),
                latitude=latitude,
                longitude=longitude
            )
            
        # Fallback local lookup
        logger.info(f"Fallback local reverse geocoding: lat {latitude}, lng {longitude}")
        if abs(latitude - 37.7749) < 0.1 and abs(longitude - -122.4194) < 0.1:
            address = "Civic Center, 1230 Market St, San Francisco, CA 94102"
        else:
            address = f"Unincorporated Area near coordinates: {latitude:.4f}, {longitude:.4f}"
            
        return ReverseGeocodeResult(address=address, latitude=latitude, longitude=longitude)

    def calculate_routing(self, from_lat: float, from_lon: float, 
                          hospital_name: str, hospital_lat: float, hospital_lon: float, 
                          incident_id: str) -> RoutingResult:
        """
        Calculates distance, travel duration, and tracking URL.
        """
        distance = self.calculate_distance(from_lat, from_lon, hospital_lat, hospital_lon)
        avg_speed_mph = 35.0
        duration = max(2, int((distance / avg_speed_mph) * 60.0))
        live_tracking_url = f"https://maps.lifelink.ai/live/{incident_id}"
        
        return RoutingResult(
            distance_miles=round(distance, 2),
            duration_minutes=duration,
            destination_hospital_name=hospital_name,
            live_tracking_url=live_tracking_url
        )
