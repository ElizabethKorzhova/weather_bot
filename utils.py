"""This module contains some utility functions for bot."""
from typing import Dict


def format_weather_message(city: str, data: Dict) -> str:
    """
    Format weather API data into a user-friendly message.

    Args:
        city (str): city name
        data (Dict): weather data
    Returns:
        str: formatted message
    """
    temperature = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    description = data["weather"][0]["description"]
    humidity = data["main"]["humidity"]

    return (
        f"🌍 Weather in {city}:\n"
        f"🌡 Temperature: {temperature}°C\n"
        f"📍 Feels like: {feels_like}°C\n"
        f"⛅️ Description: {description}\n"
        f"💧 Humidity: {humidity}%"
    )
