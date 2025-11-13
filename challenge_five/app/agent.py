"""Core AI agent logic for Alaska Snow Department chatbot with function calling."""

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, Tool, FunctionDeclaration
from typing import Optional, Dict, List
import json
from .config import PROJECT_ID, LOCATION, GEMINI_MODEL, GENERATION_TEMPERATURE, MAX_OUTPUT_TOKENS, ADS_SYSTEM_INSTRUCTION
from .rag import RAGRetriever
from .weather_api import WeatherAPIClient, ANCHORAGE_LAT, ANCHORAGE_LON
from .security import validate_input, validate_output

# Define function declarations for Gemini
search_faqs_declaration = FunctionDeclaration(
    name="search_alaska_faqs",
    description="Search Alaska Department of Snow FAQ database for information about snow services, operations, staff, policies, procedures, and general ADS information",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant FAQs"
            }
        },
        "required": ["query"]
    }
)

weather_declaration = FunctionDeclaration(
    name="get_alaska_weather",
    description="Get current weather alerts, warnings, and forecast for Alaska locations. Use when user asks about weather, current conditions, alerts, or forecasts.",
    parameters={
        "type": "object",
        "properties": {
            "latitude": {
                "type": "number",
                "description": "Latitude of location (default: 61.2181 for Anchorage)"
            },
            "longitude": {
                "type": "number",
                "description": "Longitude of location (default: -149.9003 for Anchorage)"
            }
        }
    }
)

# Create tool with both functions
alaska_tools = Tool(function_declarations=[search_faqs_declaration, weather_declaration])


class AlaskaSnowAgent:
    """AI agent for answering Alaska Snow Department questions with function calling."""
    
    def __init__(self):
        """Initialize the agent with RAG, weather API, and Gemini model."""
        # Initialize Vertex AI
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        
        # Initialize components
        self.rag = RAGRetriever()
        self.weather_client = WeatherAPIClient()
        self.model = GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=ADS_SYSTEM_INSTRUCTION,
            tools=[alaska_tools]  # Enable function calling
        )
    
    def _search_alaska_faqs(self, query: str) -> str:
        """
        Execute FAQ search function.
        
        Args:
            query: Search query
        
        Returns:
            JSON string with search results
        """
        faqs = self.rag.search_similar_faqs(query, top_k=3)
        result = {
            "found": len(faqs) > 0,
            "count": len(faqs),
            "faqs": [
                {
                    "question": faq["question"],
                    "answer": faq["answer"],
                    "relevance": f"{faq['similarity']:.2f}"
                }
                for faq in faqs
            ]
        }
        return json.dumps(result)
    
    def _get_alaska_weather(self, latitude: float = ANCHORAGE_LAT, longitude: float = ANCHORAGE_LON) -> str:
        """
        Execute weather API function.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
        
        Returns:
            JSON string with weather data
        """
        alerts = self.weather_client.get_weather_alerts("AK")
        forecast = self.weather_client.get_forecast(latitude, longitude)
        
        result = {
            "alerts": [
                {
                    "event": alert.event,
                    "severity": alert.severity,
                    "description": alert.description[:200]
                }
                for alert in alerts[:3]
            ],
            "forecast": [
                {
                    "period": f.period_name,
                    "temperature": f"{f.temperature}°{f.temperature_unit}",
                    "conditions": f.short_forecast
                }
                for f in forecast[:3]
            ]
        }
        return json.dumps(result)
    
    def _execute_function(self, function_name: str, function_args: Dict) -> str:
        """
        Execute a function call from Gemini.
        
        Args:
            function_name: Name of the function to call
            function_args: Arguments for the function
        
        Returns:
            JSON string with function results
        """
        if function_name == "search_alaska_faqs":
            return self._search_alaska_faqs(function_args.get("query", ""))
        elif function_name == "get_alaska_weather":
            lat = function_args.get("latitude", ANCHORAGE_LAT)
            lon = function_args.get("longitude", ANCHORAGE_LON)
            return self._get_alaska_weather(lat, lon)
        else:
            return json.dumps({"error": f"Unknown function: {function_name}"})
    
    def answer_question(
        self, 
        user_query: str, 
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        include_weather: bool = True
    ) -> Dict:
        """
        Answer a user question using function calling.
        
        Args:
            user_query: User's question
            latitude: Optional latitude for weather
            longitude: Optional longitude for weather
            include_weather: Whether to allow weather function calls
        
        Returns:
            Dictionary with answer, context, and metadata
        """
        response_data = {
            "question": user_query,
            "answer": "",
            "rag_context_used": False,
            "weather_data_used": False,
            "security_passed": True,
            "functions_called": [],
            "error": None
        }
        
        try:
            # Step 1: Security - Validate input
            validated_query = validate_input(user_query)
            
            # Step 2: Send query to Gemini with function calling
            chat = self.model.start_chat()
            
            response = chat.send_message(
                validated_query,
                generation_config=GenerationConfig(
                    temperature=GENERATION_TEMPERATURE,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                )
            )
            
            # Step 3: Check if Gemini wants to call functions
            function_calls_made = []
            
            while (response.candidates and 
                   response.candidates[0].content.parts and
                   response.candidates[0].content.parts[0].function_call):
                # Step 4: Execute function calls
                function_call = response.candidates[0].content.parts[0].function_call
                function_name = function_call.name
                function_args = dict(function_call.args)
                
                print(f"🔧 Function call: {function_name}({function_args})")
                function_calls_made.append(function_name)
                response_data["functions_called"] = function_calls_made  # Update immediately
                
                # Execute the function
                function_result = self._execute_function(function_name, function_args)
                print(f"   Result preview: {function_result[:200]}...")
                
                # Track which tools were used
                if function_name == "search_alaska_faqs":
                    response_data["rag_context_used"] = True
                elif function_name == "get_alaska_weather":
                    response_data["weather_data_used"] = True
                
                # Step 5: Send function results back to Gemini
                from vertexai.generative_models import Part
                
                function_response_part = Part.from_function_response(
                    name=function_name,
                    response={"result": function_result}
                )
                
                response = chat.send_message(function_response_part)
            
            # Step 6: Get final answer from Gemini
            answer_text = response.text
            response_data["functions_called"] = function_calls_made
            
            # Step 7: Security - Validate output
            validated_answer = validate_output(answer_text)
            response_data["answer"] = validated_answer
            
        except ValueError as e:
            # Security validation failed
            response_data["security_passed"] = False
            response_data["error"] = str(e)
            response_data["answer"] = "I apologize, but I cannot process this request due to security concerns. Please rephrase your question or contact ADS directly."
            
        except Exception as e:
            # Other errors
            response_data["error"] = str(e)
            response_data["answer"] = "I apologize, but I encountered an error processing your question. Please try again or contact ADS directly."
        
        return response_data

