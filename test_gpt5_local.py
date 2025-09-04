#!/usr/bin/env python3
"""
Test script for GPT-5 Response API integration
Run this to test the GPT-5 Response API locally before using real API key
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add backend to path
sys.path.append('backend')

# Load environment
load_dotenv('backend/.env.local')
load_dotenv()

def test_gpt5_response_api():
    """Test GPT-5 Response API with a simple request"""
    
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("❌ No valid OpenAI API key found!")
        print("Please set OPENAI_API_KEY in backend/.env.local")
        print("Example: OPENAI_API_KEY=sk-your-actual-api-key-here")
        return False
    
    try:
        from openai import OpenAI
        
        # Initialize client
        client = OpenAI(api_key=api_key)
        
        print("🧪 Testing GPT-5 Response API...")
        print(f"API Key: {api_key[:10]}...")
        
        # Test simple request
        response = client.responses.create(
            model="gpt-5",
            input="Hello! Please respond with a short greeting and confirm you're working.",
            text={"verbosity": "medium"},
            reasoning={"effort": "medium"}
        )
        
        print("✅ GPT-5 Response API is working!")
        print(f"Response: {response.output_text}")
        
        # Test with reasoning summary
        print("\n🧠 Testing with reasoning summary...")
        response_with_reasoning = client.responses.create(
            model="gpt-5",
            input="What is 2+2? Show your reasoning.",
            text={"verbosity": "high"},
            reasoning={"effort": "high", "summary": "auto"}
        )
        
        print("✅ Reasoning summary test passed!")
        print(f"Response: {response_with_reasoning.output_text}")
        
        # Check for reasoning summary
        for item in response_with_reasoning.output:
            if hasattr(item, "summary") and item.summary:
                print(f"Reasoning Summary: {item.summary[0].text}")
                break
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing GPT-5 Response API: {str(e)}")
        return False

def test_backend_health():
    """Test if backend is running"""
    import urllib.request
    import json
    
    try:
        with urllib.request.urlopen("http://localhost:8000/health", timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                print("✅ Backend is running!")
                print(f"Health check: {data}")
                return True
            else:
                print(f"❌ Backend health check failed: {response.status}")
                return False
    except Exception as e:
        print(f"❌ Backend is not running: {str(e)}")
        print("Start backend with: cd backend && source venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return False

def test_frontend():
    """Test if frontend is running"""
    import urllib.request
    
    try:
        with urllib.request.urlopen("http://localhost:3000", timeout=5) as response:
            if response.status == 200:
                print("✅ Frontend is running!")
                print("Visit: http://localhost:3000")
                return True
            else:
                print(f"❌ Frontend check failed: {response.status}")
                return False
    except Exception as e:
        print(f"❌ Frontend is not running: {str(e)}")
        print("Start frontend with: cd frontend && python3 -m http.server 3000")
        return False

if __name__ == "__main__":
    print("🚀 Testing Local GPT-5 Setup")
    print("=" * 40)
    
    # Test backend
    backend_ok = test_backend_health()
    
    # Test frontend
    frontend_ok = test_frontend()
    
    # Test GPT-5 API (only if backend is running)
    if backend_ok:
        gpt5_ok = test_gpt5_response_api()
    else:
        gpt5_ok = False
        print("⏭️  Skipping GPT-5 API test (backend not running)")
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    print(f"Backend: {'✅' if backend_ok else '❌'}")
    print(f"Frontend: {'✅' if frontend_ok else '❌'}")
    print(f"GPT-5 API: {'✅' if gpt5_ok else '❌'}")
    
    if backend_ok and frontend_ok:
        print("\n🎉 Local setup is ready!")
        print("Visit: http://localhost:3000")
        if gpt5_ok:
            print("GPT-5 Response API is working - you can test the full chat!")
        else:
            print("Set your OpenAI API key to test the full chat functionality.")
    else:
        print("\n⚠️  Some components are not running. Check the errors above.")
