"""Core AI agent logic for Alaska Snow Department chatbot."""

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from typing import Optional, Dict
from .config import PROJECT_ID, LOCATION, GEMINI_MODEL, GENERATION_TEMPERATURE, MAX_OUTPUT_TOKENS, ADS_SYSTEM_INSTRUCTION
from .rag import RAGRetriever
from .weather_api import WeatherAPIClient, ANCHORAGE_LAT, ANCHORAGE_LON
from .security import validate_input, validate_output


class AlaskaSnowAgent:
    """AI agent for answering Alaska Snow Department questions."""
    
    def __init__(self):
        """Initialize the agent with RAG, weather API, and Gemini model."""
        # Initialize Vertex AI
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        
        # Initialize components
        self.rag = RAGRetriever()
        self.weather_client = WeatherAPIClient()
        self.model = GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=ADS_SYSTEM_INSTRUCTION
        )
    
    def answer_question(
        self, 
        user_query: str, 
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        include_weather: bool = True
    ) -> Dict:
        """
        Answer a user question about Alaska snow services.
        
        Args:
            user_query: User's question
            latitude: Optional latitude for weather
            longitude: Optional longitude for weather
            include_weather: Whether to fetch weather data
        
        Returns:
            Dictionary with answer, context, and metadata
        """
        response_data = {
            "question": user_query,
            "answer": "",
            "rag_context_used": False,
            "weather_data_used": False,
            "security_passed": True,
            "error": None
        }
        
        try:
            # Step 1: Security - Validate input
            validated_query = validate_input(user_query)
            
            # Step 2: RAG - Search for relevant FAQs
            similar_faqs = self.rag.search_similar_faqs(validated_query, top_k=3)
            faq_context = self.rag.format_context_for_prompt(similar_faqs)
            response_data["rag_context_used"] = len(similar_faqs) > 0
            
            # Step 3: Weather - Fetch current weather data if requested
            weather_context = ""
            if include_weather:
                lat = latitude or ANCHORAGE_LAT
                lon = longitude or ANCHORAGE_LON
                
                alerts = self.weather_client.get_weather_alerts("AK")
                forecast = self.weather_client.get_forecast(lat, lon)
                
                if alerts or forecast:
                    weather_context = "\nCURRENT WEATHER INFORMATION:\n"
                    weather_context += self.weather_client.format_alerts_for_context(alerts)
                    weather_context += "\n"
                    weather_context += self.weather_client.format_forecast_for_context(forecast)
                    response_data["weather_data_used"] = True
            
            # Step 4: Build prompt with all context
            prompt = f"""Answer the user's question about the Alaska Department of Snow using the information provided below.

{faq_context}

{weather_context}

User Question: {validated_query}

Instructions:
- Use the FAQ context above to answer the question accurately
- If weather information is relevant, include it in your answer
- Be specific and cite the information from the FAQs when possible
- If the FAQs don't contain the answer, politely say you don't have that specific information
- Keep your answer clear, helpful, and focused on the user's question

Answer:"""
            
            # Step 5: Generate answer with Gemini
            gen_response = self.model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    temperature=GENERATION_TEMPERATURE,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                )
            )
            
            answer_text = gen_response.text
            
            # Step 6: Security - Validate output
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

