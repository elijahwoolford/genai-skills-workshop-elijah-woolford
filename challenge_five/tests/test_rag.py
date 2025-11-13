"""Unit tests for RAG retriever."""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag import RAGRetriever


class TestRAGRetriever:
    """Test suite for RAG retriever."""
    
    @patch('app.rag.bigquery.Client')
    def test_initialization(self, mock_bq_client):
        """Test retriever initializes correctly."""
        retriever = RAGRetriever()
        assert retriever.client is not None
        assert "ads_faqs_embedded" in retriever.embedded_table_ref
    
    @patch('app.rag.bigquery.Client')
    def test_search_similar_faqs_success(self, mock_bq_client):
        """Test successful FAQ search."""
        mock_client = Mock()
        mock_result = [
            Mock(question="Q1", answer="A1", distance=0.1),
            Mock(question="Q2", answer="A2", distance=0.2),
        ]
        mock_client.query.return_value.result.return_value = mock_result
        mock_bq_client.return_value = mock_client
        
        retriever = RAGRetriever()
        faqs = retriever.search_similar_faqs("test question", top_k=2)
        
        assert len(faqs) == 2
        assert faqs[0]["question"] == "Q1"
        assert faqs[0]["distance"] == 0.1
        assert "similarity" in faqs[0]
    
    @patch('app.rag.bigquery.Client')
    def test_format_context_empty(self, mock_bq_client):
        """Test formatting with no FAQs."""
        retriever = RAGRetriever()
        formatted = retriever.format_context_for_prompt([])
        assert "No relevant FAQ information" in formatted
    
    @patch('app.rag.bigquery.Client')
    def test_format_context_with_faqs(self, mock_bq_client):
        """Test formatting with FAQs."""
        retriever = RAGRetriever()
        faqs = [
            {"question": "When is plowing?", "answer": "Daily", "distance": 0.1}
        ]
        formatted = retriever.format_context_for_prompt(faqs)
        assert "ALASKA SNOW DEPARTMENT" in formatted
        assert "When is plowing?" in formatted
        assert "Daily" in formatted

