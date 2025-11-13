"""RAG implementation using BigQuery vector search."""

from google.cloud import bigquery
from typing import List, Dict
from .config import PROJECT_ID, DATASET_ID, EMBEDDED_TABLE_ID, EMBEDDING_MODEL_ID


class RAGRetriever:
    """Retrieves relevant FAQ context using BigQuery vector search."""
    
    def __init__(self):
        """Initialize BigQuery client."""
        self.client = bigquery.Client(project=PROJECT_ID)
        self.embedded_table_ref = f"{PROJECT_ID}.{DATASET_ID}.{EMBEDDED_TABLE_ID}"
    
    def search_similar_faqs(self, user_question: str, top_k: int = 3) -> List[Dict]:
        """
        Search for similar FAQs using BigQuery VECTOR_SEARCH.
        
        Args:
            user_question: User's query text
            top_k: Number of similar FAQs to return
        
        Returns:
            List of dictionaries with question, answer, and distance
        """
        search_sql = f"""
        SELECT 
            query.query,
            base.question,
            base.answer,
            distance
        FROM
            VECTOR_SEARCH(
                TABLE `{self.embedded_table_ref}`,
                'ml_generate_embedding_result',
                (
                    SELECT ml_generate_embedding_result, content AS query
                    FROM ML.GENERATE_EMBEDDING(
                        MODEL `{EMBEDDING_MODEL_ID}`,
                        (SELECT '{user_question}' AS content)
                    )
                ),
                top_k => {top_k},
                options => '{{"fraction_lists_to_search": 0.01}}'
            )
        """
        
        try:
            results = self.client.query(search_sql).result()
            
            similar_faqs = []
            for row in results:
                similar_faqs.append({
                    "question": row.question,
                    "answer": row.answer,
                    "distance": row.distance,
                    "similarity": 1 - row.distance
                })
            
            return similar_faqs
            
        except Exception as e:
            print(f"RAG search error: {e}")
            return []
    
    def format_context_for_prompt(self, faqs: List[Dict]) -> str:
        """
        Format retrieved FAQs as context for Gemini.
        
        Args:
            faqs: List of FAQ dictionaries
        
        Returns:
            Formatted context string
        """
        if not faqs:
            return "No relevant FAQ information found."
        
        context_parts = ["ALASKA SNOW DEPARTMENT FAQ CONTEXT:\n"]
        for i, faq in enumerate(faqs, 1):
            context_parts.append(f"FAQ {i}:")
            context_parts.append(f"Q: {faq['question']}")
            context_parts.append(f"A: {faq['answer']}")
            context_parts.append("")
        
        return "\n".join(context_parts)

