"""This module contains some utility functions for bot."""
import os
from typing import Dict

import httpx

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


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


async def show_free_models() -> None:
    """Prints available free OpenRouter models."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://openrouter.ai/api/v1/models",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            },
            timeout=10.0,
        )

    data = response.json()

    for model in data["data"]:
        pricing = model.get("pricing", {})
        prompt_price = pricing.get("prompt")
        completion_price = pricing.get("completion")

        if prompt_price == "0" and completion_price == "0":
            print(model["id"])
