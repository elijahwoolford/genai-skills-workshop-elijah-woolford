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

