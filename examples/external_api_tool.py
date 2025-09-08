"""
Example: External API Integration

This example shows how to integrate external APIs into your MCP tools.
"""

import os
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime

# Example: Weather API integration

# @mcp.tool()
async def weather_current(
    location: str,
    units: str = "metric"
) -> Dict[str, Any]:
    """
    Get current weather for a location
    
    Args:
        location: City name or coordinates
        units: Temperature units (metric/imperial)
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return {"error": "Weather API key not configured"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": location,
                    "appid": api_key,
                    "units": units
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "location": data["name"],
                "country": data["sys"]["country"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "units": units
            }
        except httpx.HTTPError as e:
            return {"error": f"Weather API error: {str(e)}"}

# Example: GitHub API integration

# @mcp.tool()
async def github_repo_info(
    owner: str,
    repo: str
) -> Dict[str, Any]:
    """
    Get information about a GitHub repository
    
    Args:
        owner: Repository owner/organization
        repo: Repository name
    """
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "full_name": data["full_name"],
                "description": data["description"],
                "stars": data["stargazers_count"],
                "forks": data["forks_count"],
                "open_issues": data["open_issues_count"],
                "language": data["language"],
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
                "topics": data.get("topics", []),
                "homepage": data.get("homepage"),
                "default_branch": data["default_branch"]
            }
        except httpx.HTTPError as e:
            return {"error": f"GitHub API error: {str(e)}"}

# Example: OpenAI API integration

# @mcp.tool()
async def ai_summarize(
    text: str,
    max_length: int = 100
) -> Dict[str, Any]:
    """
    Summarize text using AI
    
    Args:
        text: Text to summarize
        max_length: Maximum summary length in words
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OpenAI API key not configured"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": f"Summarize the following text in {max_length} words or less."
                        },
                        {
                            "role": "user",
                            "content": text
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": max_length * 2  # Rough estimate
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "summary": data["choices"][0]["message"]["content"],
                "original_length": len(text.split()),
                "summary_length": len(data["choices"][0]["message"]["content"].split()),
                "model": data["model"]
            }
        except httpx.HTTPError as e:
            return {"error": f"OpenAI API error: {str(e)}"}

# Example: Custom API with authentication

# @mcp.tool()
async def custom_api_request(
    endpoint: str,
    method: str = "GET",
    data: Dict[str, Any] = None,
    headers: Dict[str, str] = None
) -> Dict[str, Any]:
    """
    Make a request to a custom API
    
    Args:
        endpoint: API endpoint path
        method: HTTP method
        data: Request body data
        headers: Additional headers
    """
    base_url = os.getenv("CUSTOM_API_BASE_URL", "https://api.example.com")
    api_key = os.getenv("CUSTOM_API_KEY")
    
    default_headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    } if api_key else {"Content-Type": "application/json"}
    
    if headers:
        default_headers.update(headers)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=method,
                url=f"{base_url}/{endpoint}",
                headers=default_headers,
                json=data if data else None
            )
            response.raise_for_status()
            
            return {
                "status_code": response.status_code,
                "data": response.json() if response.content else None,
                "headers": dict(response.headers)
            }
        except httpx.HTTPError as e:
            return {"error": f"API request failed: {str(e)}"}

# Helper function for rate limiting
from asyncio import Semaphore

# Create a semaphore for rate limiting (e.g., max 10 concurrent requests)
api_semaphore = Semaphore(10)

# @mcp.tool()
async def rate_limited_api_call(
    url: str
) -> Dict[str, Any]:
    """
    Make a rate-limited API call
    
    Args:
        url: URL to fetch
    """
    async with api_semaphore:  # This ensures max 10 concurrent requests
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return {"data": response.json()}
            except httpx.HTTPError as e:
                return {"error": str(e)}
