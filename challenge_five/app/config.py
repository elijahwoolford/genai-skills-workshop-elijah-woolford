"""Configuration settings for Alaska Snow Department Agent."""

import os
from typing import Optional

# GCP Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "qwiklabs-gcp-01-752385122246")
LOCATION = os.getenv("GCP_REGION", "us-central1")

# BigQuery Configuration
DATASET_ID = "alaska_snow_dataset"
TABLE_ID = "ads_faqs"
EMBEDDED_TABLE_ID = "ads_faqs_embedded"
EMBEDDING_MODEL_ID = f"{PROJECT_ID}.{DATASET_ID}.embedding_model"
BQ_CONNECTION_ID = "vertex-ai-connection"

# Model Armor Configuration
MODEL_ARMOR_TEMPLATE_ID = "alaska-snow-guard"
MODEL_ARMOR_USER_ENDPOINT = (
    f"https://modelarmor.{LOCATION}.rep.googleapis.com/v1/"
    f"projects/{PROJECT_ID}/locations/{LOCATION}/templates/{MODEL_ARMOR_TEMPLATE_ID}:sanitizeUserPrompt"
)
MODEL_ARMOR_RESPONSE_ENDPOINT = (
    f"https://modelarmor.{LOCATION}.rep.googleapis.com/v1/"
    f"projects/{PROJECT_ID}/locations/{LOCATION}/templates/{MODEL_ARMOR_TEMPLATE_ID}:sanitizeModelResponse"
)

# Gemini Configuration
GEMINI_MODEL = "gemini-2.5-pro"
GENERATION_TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 1024

# National Weather Service API
NWS_API_BASE = "https://api.weather.gov"
WEATHER_CACHE_TTL = 300  # 5 minutes in seconds

# Application Configuration
APP_PORT = int(os.getenv("PORT", "8080"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ADS System Instruction
ADS_SYSTEM_INSTRUCTION = """You are an AI assistant for the Alaska Department of Snow (ADS).
Your role is to help citizens with questions about ADS services, operations, and winter weather in Alaska.

You can answer questions about:
- Snow removal services and schedules
- Road conditions and closures
- School closures and weather impacts
- ADS organizational information (history, staff, budget, operations)
- Winter safety and emergency procedures
- Current weather alerts and forecasts
- How to contact ADS offices
- Employment and volunteer opportunities

Guidelines:
1. Answer based on the FAQ context and weather data provided
2. Be helpful, professional, and accurate
3. Include weather information when relevant
4. If the provided context doesn't contain the answer, say so politely
5. Do not make up information - only use the provided context

Base all answers on the FAQ context and weather data provided in the prompt."""

