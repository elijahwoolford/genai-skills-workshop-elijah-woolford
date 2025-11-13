"""Streamlit UI for Alaska Snow Department Agent."""

import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent import AlaskaSnowAgent
from app.weather_api import ANCHORAGE_LAT, ANCHORAGE_LON

# Page configuration
st.set_page_config(
    page_title="Alaska Snow Department Assistant",
    page_icon="❄️",
    layout="wide"
)

# Initialize agent (cached)
@st.cache_resource
def get_agent():
    return AlaskaSnowAgent()


# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .question-box {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }
    .answer-box {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>❄️ Alaska Department of Snow</h1>
    <h3>AI Assistant for Snow Services</h3>
    <p>Get answers about snow removal, road conditions, closures, and weather</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.write("""
    This AI assistant helps answer questions about:
    - Snow plowing schedules
    - Road conditions
    - School closures
    - Winter safety
    - Current weather alerts
    """)
    
    st.divider()
    
    st.header("📍 Location (Optional)")
    use_location = st.checkbox("Include weather for specific location", value=False)
    
    latitude = None
    longitude = None
    
    if use_location:
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.number_input("Latitude", value=ANCHORAGE_LAT, format="%.4f")
        with col2:
            longitude = st.number_input("Longitude", value=ANCHORAGE_LON, format="%.4f")
        
        st.caption("Default: Anchorage, AK")
    
    st.divider()
    
    st.header("🔒 Security")
    st.write("All queries are validated with Model Armor for security.")
    
    st.divider()
    
    st.caption("Powered by Gemini 2.5 Pro")

# Main content
st.header("Ask a Question")

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Check if there's a pending question from a button click
process_question = None

# Display conversation history
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "metadata" in message and message["metadata"]:
            with st.expander("Details"):
                st.json(message["metadata"])
    
    # Check if last message is unanswered user question
    if (i == len(st.session_state.messages) - 1 and 
        message["role"] == "user" and 
        (i == 0 or st.session_state.messages[i-1]["role"] == "assistant")):
        # This is a new question that needs answering
        process_question = message["content"]

# Chat input
if prompt := st.chat_input("Type your question about snow services..."):
    process_question = prompt
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

# Process question if we have one (from input or button)
if process_question:
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                agent_instance = get_agent()
                result = agent_instance.answer_question(
                    user_query=process_question,
                    latitude=latitude,
                    longitude=longitude,
                    include_weather=use_location or True  # Always try to include weather
                )
                
                # Display answer
                st.markdown(result["answer"])
                
                # Show metadata
                metadata = {
                    "FAQ Context Used": result["rag_context_used"],
                    "Weather Data Used": result["weather_data_used"],
                    "Security Check": "✓ Passed" if result["security_passed"] else "✗ Failed"
                }
                
                if result.get("error"):
                    st.error(f"Note: {result['error']}")
                
                # Store in history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "metadata": metadata
                })
                
            except Exception as e:
                error_msg = f"I apologize, but I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "metadata": None
                })

# Quick questions
st.divider()
st.subheader("💡 Try these questions:")

example_questions = [
    "When will my street be plowed?",
    "Are there any current weather alerts?",
    "What should I do if my car gets stuck in snow?",
    "How do I report a snow emergency?",
]

cols = st.columns(2)
for i, question in enumerate(example_questions):
    with cols[i % 2]:
        if st.button(question, key=f"example_{i}"):
            st.session_state.messages.append({"role": "user", "content": question})
            st.rerun()

# Footer
st.divider()
st.caption("Alaska Department of Snow - AI Assistant | Powered by Vertex AI")

