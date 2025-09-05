#!/usr/bin/env python3
"""
Test script to debug image upload and chat functionality
"""

import requests
import json

# Test the image upload endpoint
def test_image_upload():
    print("=== Testing Image Upload ===")
    
    # Create a simple test image (1x1 pixel PNG)
    test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    
    try:
        response = requests.post(
            'http://localhost:8000/api/upload-image',
            files={'file': ('test.png', test_image_data, 'image/png')},
            headers={'x-filename': 'test.png'}
        )
        print(f"Upload Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Upload Result: {result}")
            return result.get('url')
        else:
            print(f"Upload Error: {response.text}")
            return None
    except Exception as e:
        print(f"Upload Exception: {e}")
        return None

# Test the chat endpoint with image
def test_chat_with_image(image_url):
    print("\n=== Testing Chat with Image ===")
    
    chat_data = {
        "bot_id": "mktg_strategist",
        "messages": [{"role": "user", "content": "What's in this image?"}],
        "image_url": image_url,
        "temperature": 0.3,
        "verbosity": "medium"
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/v1/chat',
            json=chat_data,
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer c17e4ea45486a836e15eae268ecc5043312c96f5bec19a9fc9f1452f30b361bd'
            }
        )
        print(f"Chat Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Chat Response: {result}")
        else:
            print(f"Chat Error: {response.text}")
    except Exception as e:
        print(f"Chat Exception: {e}")

if __name__ == "__main__":
    print("Starting image upload and chat test...")
    
    # Test image upload
    image_url = test_image_upload()
    
    if image_url:
        # Test chat with image
        test_chat_with_image(image_url)
    else:
        print("Image upload failed, skipping chat test")
