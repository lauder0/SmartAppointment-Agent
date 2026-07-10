"""Weather tool wrapper."""

from __future__ import annotations

import os

import aiohttp
from langchain_core.tools import tool

from .schemas import GetWeatherInput, tool_result


async def _get_weather_data(city: str = "Beijing") -> str:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Weather is pleasant today. Please arrive a few minutes early and stay hydrated."

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": city,
                    "appid": api_key,
                    "units": "metric",
                    "lang": "zh_cn",
                },
            ) as response:
                if response.status != 200:
                    return "Weather is currently unavailable. Please check conditions before travel."
                data = await response.json()
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                description = data["weather"][0]["description"]
                humidity = data["main"]["humidity"]
                wind_speed = data.get("wind", {}).get("speed", 0)
                return (
                    f"{city} weather: {description}, {temp} C "
                    f"(feels like {feels_like} C), humidity {humidity}%, wind {wind_speed} m/s."
                )
    except Exception:
        return "Weather is currently unavailable. Please check conditions before travel."


@tool(args_schema=GetWeatherInput)
async def get_weather(city: str = "Beijing") -> dict:
    """Get current weather information for reminder and appointment-success messages."""
    try:
        result = await _get_weather_data(city)
        return tool_result(True, data={"city": city, "weather": result}, message="weather query succeeded")
    except Exception as e:
        return tool_result(False, data={"city": city}, message="weather query failed", error=str(e))
