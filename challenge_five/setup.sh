#!/bin/bash
# Setup script for Alaska Snow Department Agent

echo "=================================================="
echo "Alaska Snow Department Agent - Setup"
echo "=================================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "✓ gcloud CLI found"

# Set project
echo ""
echo "Setting GCP project..."
gcloud config set project qwiklabs-gcp-01-752385122246

# Authenticate
echo ""
echo "Authenticating..."
gcloud auth application-default login

# Enable APIs
echo ""
echo "Enabling required APIs..."
gcloud services enable aiplatform.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable cloudtrace.googleapis.com
gcloud services enable modelarmor.googleapis.com

# Create Python virtual environment
echo ""
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=================================================="
echo "✓ Setup complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Load data: python data/load_ads_data.py"
echo "3. Run tests: pytest tests/ -v"
echo "4. Start app: streamlit run frontend/streamlit_app.py"
echo ""

