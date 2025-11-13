"""National Weather Service API client with caching."""

import requests
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class WeatherAlert:
    """Weather alert data structure."""
    event: str
    severity: str
    description: str
    instruction: str


@dataclass
class Forecast:
    """Weather forecast data structure."""
    period_name: str
    temperature: int
    temperature_unit: str
    short_forecast: str
    detailed_forecast: str


class WeatherAPIClient:
    """Client for National Weather Service API with caching."""
    
    def __init__(self, cache_ttl: int = 300):
        """
        Initialize weather API client.
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default 5 minutes)
        """
        self.base_url = "https://api.weather.gov"
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Tuple[datetime, any]] = {}
        self.headers = {
            "User-Agent": "(Alaska Snow Department Agent, contact@ads.alaska.gov)",
            "Accept": "application/json"
        }
    
    def _get_cached(self, key: str) -> Optional[any]:
        """Get cached data if not expired."""
        if key in self._cache:
            timestamp, data = self._cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return data
            else:
                del self._cache[key]
        return None
    
    def _set_cache(self, key: str, data: any):
        """Store data in cache."""
        self._cache[key] = (datetime.now(), data)
    
    def get_weather_alerts(self, state: str = "AK") -> List[WeatherAlert]:
        """
        Get active weather alerts for Alaska.
        
        Args:
            state: State code (default "AK" for Alaska)
        
        Returns:
            List of WeatherAlert objects
        """
        cache_key = f"alerts_{state}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            url = f"{self.base_url}/alerts/active?area={state}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            alerts = []
            
            for feature in data.get("features", [])[:5]:  # Limit to 5 alerts
                props = feature.get("properties", {})
                alert = WeatherAlert(
                    event=props.get("event", "Unknown Event"),
                    severity=props.get("severity", "Unknown"),
                    description=props.get("description", "")[:500],  # Limit length
                    instruction=props.get("instruction", "")[:300]
                )
                alerts.append(alert)
            
            self._set_cache(cache_key, alerts)
            return alerts
            
        except Exception as e:
            print(f"Weather alert error: {e}")
            return []
    
    def get_forecast(self, lat: float, lon: float) -> List[Forecast]:
        """
        Get weather forecast for a location.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            List of Forecast objects (up to 7 periods)
        """
        cache_key = f"forecast_{lat}_{lon}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            # First, get the forecast URL for this location
            points_url = f"{self.base_url}/points/{lat},{lon}"
            points_response = requests.get(points_url, headers=self.headers, timeout=10)
            points_response.raise_for_status()
            points_data = points_response.json()
            
            forecast_url = points_data["properties"]["forecast"]
            
            # Now get the actual forecast
            forecast_response = requests.get(forecast_url, headers=self.headers, timeout=10)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            forecasts = []
            for period in forecast_data["properties"]["periods"][:7]:  # Next 7 periods
                forecast = Forecast(
                    period_name=period.get("name", ""),
                    temperature=period.get("temperature", 0),
                    temperature_unit=period.get("temperatureUnit", "F"),
                    short_forecast=period.get("shortForecast", ""),
                    detailed_forecast=period.get("detailedForecast", "")
                )
                forecasts.append(forecast)
            
            self._set_cache(cache_key, forecasts)
            return forecasts
            
        except Exception as e:
            print(f"Forecast error: {e}")
            return []
    
    def format_alerts_for_context(self, alerts: List[WeatherAlert]) -> str:
        """Format alerts as text for Gemini context."""
        if not alerts:
            return "No active weather alerts."
        
        alert_text = "ACTIVE WEATHER ALERTS:\n"
        for i, alert in enumerate(alerts, 1):
            alert_text += f"\n{i}. {alert.event} ({alert.severity})\n"
            alert_text += f"   {alert.description[:200]}...\n"
        
        return alert_text
    
    def format_forecast_for_context(self, forecasts: List[Forecast]) -> str:
        """Format forecast as text for Gemini context."""
        if not forecasts:
            return "Forecast not available."
        
        forecast_text = "WEATHER FORECAST:\n"
        for forecast in forecasts[:3]:  # Next 3 periods
            forecast_text += f"\n{forecast.period_name}: {forecast.temperature}°{forecast.temperature_unit}\n"
            forecast_text += f"  {forecast.short_forecast}\n"
        
        return forecast_text


# Default Alaska coordinates (Anchorage)
ANCHORAGE_LAT = 61.2181
ANCHORAGE_LON = -149.9003

