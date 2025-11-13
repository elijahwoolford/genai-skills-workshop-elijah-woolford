"""
Create Model Armor template for Alaska Snow Department Agent.

Run this script once to create the security template.
"""

import requests
import google.auth
from google.auth.transport.requests import Request
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import PROJECT_ID, LOCATION, MODEL_ARMOR_TEMPLATE_ID


def create_model_armor_template():
    """Create the alaska-snow-guard Model Armor template."""
    # Get access token
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())
    token = credentials.token
    
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}"
    create_url = f"https://modelarmor.{LOCATION}.rep.googleapis.com/v1/{parent}/templates?templateId={MODEL_ARMOR_TEMPLATE_ID}"
    
    template_config = {
        "filterConfig": {
            "piAndJailbreakFilterSettings": {
                "filterEnforcement": "ENABLED",
                "confidenceLevel": "LOW_AND_ABOVE"
            }
        }
    }
    
    print(f"Creating Model Armor template: {MODEL_ARMOR_TEMPLATE_ID}")
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print()
    
    try:
        response = requests.post(
            create_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=template_config,
            timeout=30,
        )
        
        if response.status_code in [200, 201]:
            print(f"✓ Template created successfully!")
            result = response.json()
            print(f"  Template name: {result.get('name', 'N/A')}")
        elif response.status_code == 409:
            print(f"✓ Template already exists: {MODEL_ARMOR_TEMPLATE_ID}")
        else:
            print(f"✗ Error creating template: {response.status_code}")
            print(f"  Response: {response.text}")
            print()
            print("Alternative: Create via Cloud Console:")
            print(f"  https://console.cloud.google.com/security/model-armor/templates?project={PROJECT_ID}")
            return False
            
    except Exception as e:
        print(f"✗ Exception: {e}")
        print()
        print("Alternative: Create via Cloud Console:")
        print(f"  https://console.cloud.google.com/security/model-armor/templates?project={PROJECT_ID}")
        return False
    
    return True


if __name__ == "__main__":
    print("="*70)
    print("MODEL ARMOR TEMPLATE SETUP")
    print("="*70)
    print()
    
    success = create_model_armor_template()
    
    print()
    print("="*70)
    if success:
        print("✓ Setup complete! You can now run the application.")
    else:
        print("⚠ Please create the template manually or check permissions.")
    print("="*70)

