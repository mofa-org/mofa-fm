#!/usr/bin/env python3
"""
Mock Weather MCP Server
Provides weather-like responses for testing without real API keys
"""

import json
import sys
import random
from datetime import datetime

class MockWeatherServer:
    """Mock weather server that provides simulated weather data"""
    
    def __init__(self):
        self.weather_conditions = [
            "sunny", "partly cloudy", "cloudy", "overcast", 
            "light rain", "moderate rain", "heavy rain",
            "light snow", "moderate snow", "foggy", "clear"
        ]
        
    def get_mock_weather(self, location):
        """Generate mock weather data for a location"""
        # Use location hash for consistent but varied results
        seed = sum(ord(c) for c in location)
        random.seed(seed + datetime.now().hour)
        
        temp_c = random.randint(-10, 35)
        temp_f = int(temp_c * 9/5 + 32)
        condition = random.choice(self.weather_conditions)
        humidity = random.randint(30, 90)
        wind_kph = random.randint(0, 40)
        wind_mph = int(wind_kph * 0.621371)
        
        return {
            "location": location,
            "temperature": {
                "celsius": temp_c,
                "fahrenheit": temp_f
            },
            "condition": condition,
            "humidity": f"{humidity}%",
            "wind": {
                "kph": wind_kph,
                "mph": wind_mph,
                "direction": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])
            },
            "feels_like": {
                "celsius": temp_c + random.randint(-3, 3),
                "fahrenheit": temp_f + random.randint(-5, 5)
            },
            "visibility_km": random.randint(5, 20),
            "uv_index": random.randint(1, 11),
            "last_updated": datetime.now().isoformat()
        }
    
    def handle_request(self, request):
        """Handle MCP protocol requests"""
        if request.get("method") == "tools/list":
            return {
                "tools": [
                    {
                        "name": "get_current_weather",
                        "description": "Get mock weather data for testing",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "location": {
                                    "type": "string",
                                    "description": "City name or location"
                                }
                            },
                            "required": ["location"]
                        }
                    }
                ]
            }
        
        elif request.get("method") == "tools/call":
            tool_name = request.get("params", {}).get("name")
            args = request.get("params", {}).get("arguments", {})
            
            if tool_name == "get_current_weather":
                location = args.get("location", "Unknown")
                weather_data = self.get_mock_weather(location)
                
                # Format as friendly text
                result = (
                    f"Current weather in {location}:\n"
                    f"Temperature: {weather_data['temperature']['celsius']}°C "
                    f"({weather_data['temperature']['fahrenheit']}°F)\n"
                    f"Condition: {weather_data['condition']}\n"
                    f"Humidity: {weather_data['humidity']}\n"
                    f"Wind: {weather_data['wind']['kph']} km/h from {weather_data['wind']['direction']}\n"
                    f"Visibility: {weather_data['visibility_km']} km\n"
                    f"UV Index: {weather_data['uv_index']}"
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ],
                    "raw_data": weather_data
                }
        
        return {"error": "Unknown request"}

def main():
    """Run as MCP server via stdio"""
    server = MockWeatherServer()
    
    # Log to stderr for debugging
    sys.stderr.write("Mock weather server started\n")
    sys.stderr.flush()
    
    # MCP stdio protocol
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            request = json.loads(line)
            sys.stderr.write(f"Received request: {json.dumps(request)}\n")
            sys.stderr.flush()
            
            # Skip notifications (they don't need responses)
            if request.get("method", "").startswith("notifications/"):
                continue
            
            # Handle initialization request
            if request.get("method") == "initialize":
                result = {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "mock-weather-server",
                        "version": "1.0.0"
                    }
                }
                print(json.dumps({
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": result
                }))
            else:
                response = server.handle_request(request)
                print(json.dumps({
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": response
                }))
            sys.stdout.flush()
            
        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }), file=sys.stderr)
            sys.stderr.flush()

if __name__ == "__main__":
    main()