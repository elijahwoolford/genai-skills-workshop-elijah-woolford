"""Unit tests for weather API client."""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.weather_api import WeatherAPIClient, WeatherAlert, Forecast


class TestWeatherAPIClient:
    """Test suite for WeatherAPIClient."""
    
    def test_initialization(self):
        """Test client initializes correctly."""
        client = WeatherAPIClient(cache_ttl=60)
        assert client.cache_ttl == 60
        assert client.base_url == "https://api.weather.gov"
    
    @patch('app.weather_api.requests.get')
    def test_get_weather_alerts_success(self, mock_get):
        """Test successful weather alert retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "event": "Winter Storm Warning",
                        "severity": "Severe",
                        "description": "Heavy snow expected",
                        "instruction": "Avoid travel"
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        client = WeatherAPIClient()
        alerts = client.get_weather_alerts("AK")
        
        assert len(alerts) == 1
        assert alerts[0].event == "Winter Storm Warning"
        assert alerts[0].severity == "Severe"
    
    @patch('app.weather_api.requests.get')
    def test_get_weather_alerts_error(self, mock_get):
        """Test alert retrieval handles errors gracefully."""
        mock_get.side_effect = Exception("API Error")
        
        client = WeatherAPIClient()
        alerts = client.get_weather_alerts("AK")
        
        assert alerts == []
    
    def test_format_alerts_empty(self):
        """Test formatting with no alerts."""
        client = WeatherAPIClient()
        formatted = client.format_alerts_for_context([])
        assert "No active weather alerts" in formatted
    
    def test_format_alerts_with_data(self):
        """Test formatting with alerts."""
        client = WeatherAPIClient()
        alerts = [WeatherAlert("Snow", "Moderate", "Heavy snow", "Stay home")]
        formatted = client.format_alerts_for_context(alerts)
        assert "ACTIVE WEATHER ALERTS" in formatted
        assert "Snow" in formatted

