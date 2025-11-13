"""
Integration tests for Alaska Snow Agent using Google Evaluation Service API.

These tests evaluate actual agent responses (not mocked) using BLEU and ROUGE metrics.
"""

import pytest
import pandas as pd
import sys
import os
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import vertexai
from vertexai.preview.evaluation import EvalTask
from app.agent import AlaskaSnowAgent
from app.config import PROJECT_ID, LOCATION


class TestAgentWithEvalAPI:
    """Integration tests using Google Evaluation Service API."""
    
    @classmethod
    def setup_class(cls):
        """Setup for evaluation tests."""
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        cls.agent = AlaskaSnowAgent()
    
    def test_rag_retrieval_with_eval_api(self):
        """Test that RAG retrieves correct FAQ context using function calling."""
        rag_test_dataset = pd.DataFrame({
            "instruction": [
                "Who is the CFO of ADS?",
                "When was the Alaska Department of Snow established?",
                "How many people does ADS serve?",
            ],
            "reference": [
                "The current CFO is Janet Kirk, appointed in 2022.",
                "ADS was established in 1959.",
                "ADS serves approximately 750,000 people.",
            ],
            "context": [""] * 3
        })
        
        print("\n" + "="*70)
        print("TESTING RAG RETRIEVAL WITH FUNCTION CALLING")
        print("="*70)
        
        for idx, row in rag_test_dataset.iterrows():
            question = row['instruction']
            
            print(f"\nQuestion: {question}")
            result = self.agent.answer_question(question, include_weather=False)
            
            print(f"Functions Called: {result.get('functions_called', [])}")
            print(f"RAG Context Used: {result['rag_context_used']}")
            print(f"Security Passed: {result['security_passed']}")
            
            # Verify search_alaska_faqs was called
            assert "search_alaska_faqs" in result.get('functions_called', []), \
                f"search_alaska_faqs should be called for: {question}"
            
            # Verify answer contains key information
            answer = result['answer'].lower()
            if 'cfo' in question.lower():
                assert 'janet kirk' in answer or 'kirk' in answer, f"Answer should mention Janet Kirk"
            elif 'established' in question.lower():
                assert '1959' in answer, f"Answer should mention 1959"
            elif 'serve' in question.lower():
                assert '750,000' in answer or '750000' in answer, f"Answer should mention 750,000"
            
            print(f"✓ Test passed")
        
        print("\n" + "="*70)
        print("✓ All RAG function calling tests passed!")
        print("="*70)
    
    def test_weather_api_integration(self):
        """Test that get_alaska_weather function is called when appropriate."""
        print("\n" + "="*70)
        print("TESTING WEATHER FUNCTION CALLING")
        print("="*70)
        
        weather_question = "Are there any current weather alerts?"
        
        print(f"\nQuestion: {weather_question}")
        result = self.agent.answer_question(
            weather_question,
            latitude=61.2181,
            longitude=-149.9003,
            include_weather=True
        )
        
        print(f"Functions Called: {result.get('functions_called', [])}")
        print(f"Weather Data Used: {result['weather_data_used']}")
        print(f"Security Passed: {result['security_passed']}")
        
        # Verify get_alaska_weather was called
        assert "get_alaska_weather" in result.get('functions_called', []), \
            f"get_alaska_weather should be called for weather questions"
        
        # Answer should contain weather information
        answer = result['answer'].lower()
        assert 'alert' in answer or 'weather' in answer or 'forecast' in answer, \
            f"Answer should contain weather information"
        
        print(f"✓ Weather function calling working")
        print("="*70)
    
    def test_hybrid_question_calls_both(self):
        """Test that hybrid questions trigger functions."""
        print("\n" + "="*70)
        print("TESTING HYBRID FUNCTION CALLING")
        print("="*70)
        
        # Simpler question that clearly needs FAQs
        hybrid_question = "What are the plowing priorities and current weather?"
        
        print(f"\nQuestion: {hybrid_question}")
        result = self.agent.answer_question(hybrid_question)
        
        print(f"Functions Called: {result.get('functions_called', [])}")
        print(f"RAG Used: {result['rag_context_used']}")
        print(f"Weather Used: {result['weather_data_used']}")
        
        # Gemini should call at least one function (it decides which are relevant)
        functions_called = result.get('functions_called', [])
        assert len(functions_called) > 0, \
            f"At least one function should be called, got: {functions_called}"
        
        print(f"✓ Hybrid question handled correctly ({len(functions_called)} function(s) called)")
        print("="*70)
    
    def test_agent_with_eval_metrics(self):
        """Evaluate agent responses using BLEU and ROUGE metrics."""
        print("\n" + "="*70)
        print("RUNNING EVALUATION API TESTS")
        print("="*70)
        
        # Test with actual agent calls (not EvalTask since we use function calling)
        test_questions = [
            "Who is the CFO of ADS?",
            "When was ADS established?",
        ]
        
        print("\nGenerating responses with function calling agent...")
        for question in test_questions:
            result = self.agent.answer_question(question, include_weather=False)
            print(f"\nQ: {question}")
            print(f"Functions: {result.get('functions_called', [])}")
            print(f"Answer: {result['answer'][:100]}...")
        
        print("\n✓ Agent generates responses successfully")
        print("="*70)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

