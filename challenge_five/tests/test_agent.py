"""Unit tests for Alaska Snow Agent."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent import AlaskaSnowAgent


class TestAlaskaSnowAgent:
    """Test suite for Alaska Snow Agent."""
    
    @patch('app.agent.vertexai.init')
    @patch('app.agent.RAGRetriever')
    @patch('app.agent.WeatherAPIClient')
    @patch('app.agent.GenerativeModel')
    def test_agent_initialization(self, mock_model, mock_weather, mock_rag, mock_vertex):
        """Test agent initializes all components."""
        agent = AlaskaSnowAgent()
        
        assert agent.rag is not None
        assert agent.weather_client is not None
        assert agent.model is not None
    
    @patch('app.agent.validate_input')
    @patch('app.agent.validate_output')
    @patch('app.agent.RAGRetriever')
    @patch('app.agent.WeatherAPIClient')
    @patch('app.agent.GenerativeModel')
    @patch('app.agent.vertexai.init')
    def test_answer_question_basic(self, mock_vertex, mock_model_cls, mock_weather_cls, mock_rag_cls, mock_val_out, mock_val_in):
        """Test basic question answering."""
        # Setup mocks
        mock_val_in.return_value = "When is plowing?"
        mock_val_out.return_value = "Plowing occurs daily."
        
        mock_rag = Mock()
        mock_rag.search_similar_faqs.return_value = [
            {"question": "Q1", "answer": "A1", "distance": 0.1}
        ]
        mock_rag.format_context_for_prompt.return_value = "FAQ Context"
        mock_rag_cls.return_value = mock_rag
        
        mock_weather = Mock()
        mock_weather.get_weather_alerts.return_value = []
        mock_weather.get_forecast.return_value = []
        mock_weather.format_alerts_for_context.return_value = "No alerts"
        mock_weather.format_forecast_for_context.return_value = "No forecast"
        mock_weather_cls.return_value = mock_weather
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Plowing occurs daily."
        mock_model.generate_content.return_value = mock_response
        mock_model_cls.return_value = mock_model
        
        # Test
        agent = AlaskaSnowAgent()
        result = agent.answer_question("When is plowing?")
        
        assert result["answer"] == "Plowing occurs daily."
        assert result["security_passed"] == True
        assert "error" in result
    
    @patch('app.agent.validate_input')
    @patch('app.agent.RAGRetriever')
    @patch('app.agent.WeatherAPIClient')
    @patch('app.agent.GenerativeModel')
    @patch('app.agent.vertexai.init')
    def test_answer_question_security_block(self, mock_vertex, mock_model_cls, mock_weather_cls, mock_rag_cls, mock_val_in):
        """Test that security blocks work."""
        mock_val_in.side_effect = ValueError("Blocked by Model Armor")
        
        agent = AlaskaSnowAgent()
        result = agent.answer_question("Malicious query")
        
        assert result["security_passed"] == False
        assert "security concerns" in result["answer"].lower()

