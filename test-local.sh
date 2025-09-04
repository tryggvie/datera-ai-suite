#!/bin/bash

# AI Assistants Suite - Local Test Script
# This script tests the local development setup

echo "🧪 AI Assistants Suite - Local Testing"
echo "======================================"

# Test backend health endpoint
echo "🔍 Testing backend health endpoint..."
cd backend

# Start backend in background
echo "🚀 Starting backend server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Test health endpoint
echo "📡 Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if echo "$HEALTH_RESPONSE" | grep -q '"status":"ok"'; then
    echo "✅ Backend health check passed"
else
    echo "❌ Backend health check failed"
    echo "Response: $HEALTH_RESPONSE"
fi

# Test chat endpoint (should fail without auth)
echo "🔐 Testing chat endpoint authentication..."
CHAT_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/v1/chat \
    -H "Content-Type: application/json" \
    -d '{"messages":[{"role":"user","content":"test"}],"bot_id":"general"}')

if [ "$CHAT_RESPONSE" = "401" ]; then
    echo "✅ Chat endpoint authentication working (401 as expected)"
else
    echo "❌ Chat endpoint authentication failed (got $CHAT_RESPONSE, expected 401)"
fi

# Stop backend
echo "🛑 Stopping backend server..."
kill $BACKEND_PID

cd ..

# Test frontend files
echo "🌐 Testing frontend files..."
if [ -f "frontend/index.html" ]; then
    echo "✅ Frontend index.html exists"
else
    echo "❌ Frontend index.html missing"
fi

if [ -f "frontend/public/bots.config.json" ]; then
    echo "✅ Bot configuration exists"
else
    echo "❌ Bot configuration missing"
fi

# Test JSON validity
echo "📋 Testing bot configuration JSON..."
if python3 -m json.tool frontend/public/bots.config.json > /dev/null 2>&1; then
    echo "✅ Bot configuration JSON is valid"
else
    echo "❌ Bot configuration JSON is invalid"
fi

echo ""
echo "🎯 Local testing complete!"
echo ""
echo "To start development:"
echo "1. Backend: cd backend && uvicorn app.main:app --reload"
echo "2. Frontend: cd frontend && python3 -m http.server 8000"
echo "3. Open http://localhost:8000 in your browser"
