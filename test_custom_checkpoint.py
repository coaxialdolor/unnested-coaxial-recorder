#!/usr/bin/env python3
"""
Test custom checkpoint speech generation
"""
import requests
import json

# Test the speech generation endpoint with custom checkpoint
url = "http://localhost:8000/api/test/generate"

# Test data with custom checkpoint
test_data = {
    "language": "sv-SE",
    "voice_id": "custom:models/checkpoints/final_model.ckpt",
    "text": "Hej, detta är en test av röstsyntes med min tränade modell.",
    "length_scale": 1.0,
    "noise_scale": 0.667
}

print("Testing speech generation with custom checkpoint...")
print(f"URL: {url}")
print(f"Data: {json.dumps(test_data, indent=2)}")
print()

try:
    response = requests.post(url, data=test_data, timeout=60)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ SUCCESS!")
        print(f"Audio URL: {result.get('audio_url')}")
        print(f"Filename: {result.get('filename')}")
        print(f"Language: {result.get('language')}")
        print(f"Voice ID: {result.get('voice_id')}")
    else:
        print("\n❌ FAILED!")
        print(f"Error: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"\n❌ REQUEST FAILED!")
    print(f"Error: {e}")

