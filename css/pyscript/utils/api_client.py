"""
API Client for making requests to the server
"""
import json
import asyncio
from pyodide.http import pyfetch
from ..config import API_BASE_URL, API_TIMEOUT

class APIClient:
    """Client for making API requests"""
    
    @staticmethod
    async def get(endpoint, params=None):
        """
        Make a GET request to the API
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Optional query parameters
            
        Returns:
            API response as Python object
        """
        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
        
        # Add query parameters if provided
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{url}?{query_string}"
        
        try:
            response = await pyfetch(
                url=url,
                method="GET",
                headers={"Content-Type": "application/json"},
                timeout=API_TIMEOUT
            )
            
            if response.status >= 400:
                print(f"API Error ({response.status}): {await response.text()}")
                return None
                
            return await response.json()
        except Exception as e:
            print(f"API Request Failed: {str(e)}")
            return None
    
    @staticmethod
    async def post(endpoint, data):
        """
        Make a POST request to the API
        
        Args:
            endpoint: API endpoint (without base URL)
            data: Data to send in the request body
            
        Returns:
            API response as Python object
        """
        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            response = await pyfetch(
                url=url,
                method="POST",
                body=json.dumps(data),
                headers={"Content-Type": "application/json"},
                timeout=API_TIMEOUT
            )
            
            if response.status >= 400:
                print(f"API Error ({response.status}): {await response.text()}")
                return None
                
            return await response.json()
        except Exception as e:
            print(f"API Request Failed: {str(e)}")
            return None

