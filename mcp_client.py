import httpx
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self, base_url: str = "http://mim-mcp-alb-1505151310.us-east-1.elb.amazonaws.com"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)
    
    def analyze_logo(self, logo_url: str) -> Dict[str, Any]:
        """Analyze a logo using OpenAI Vision API"""
        try:
            response = self.client.post(
                f"{self.base_url}/analyze_logo",
                json={"logo_url": logo_url}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error analyzing logo: {e}")
            return {"error": str(e)}
    
    def suggest_products(self, team_name: str, sport: str = "") -> Dict[str, Any]:
        """Get product suggestions for a team"""
        try:
            response = self.client.post(
                f"{self.base_url}/suggest_products",
                json={
                    "team_name": team_name,
                    "sport": sport,
                    "target_audience": "youth_sports"
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting product suggestions: {e}")
            return {"error": str(e)}
    
    def create_team_mockup(self, logo_url: str, product_id: str, team_name: str, sport: str = "", color: str = "") -> Dict[str, Any]:
        """Create a team mockup using the MCP server"""
        try:
            payload = {
                "logo_url": logo_url,
                "product_id": product_id,
                "team_name": team_name,
                "sport": sport
            }
            if color:
                payload["color"] = color
                
            response = self.client.post(
                f"{self.base_url}/create_mockup",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error creating team mockup: {e}")
            return {"error": str(e)}
    
    def get_analytics(self, team_name: str = "") -> Dict[str, Any]:
        """Get analytics for team orders"""
        try:
            response = self.client.post(
                f"{self.base_url}/get_analytics",
                json={"team_name": team_name}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {"error": str(e)}
    
    def bulk_order_handler(self, team_name: str, product_ids: list, quantities: list) -> Dict[str, Any]:
        """Handle bulk orders for teams"""
        try:
            response = self.client.post(
                f"{self.base_url}/bulk_order",
                json={
                    "team_name": team_name,
                    "product_ids": product_ids,
                    "quantities": quantities
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error handling bulk order: {e}")
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check MCP server health"""
        try:
            response = self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error checking health: {e}")
            return {"error": str(e)}

# Global instance
mcp_client = MCPClient() 