# Backend API

FastAPI-based chatbot backend deployed on Railway.

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file from `.env.example`:
```bash
cp .env.example .env
```

3. Set your environment variables in `.env`

4. Run the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /health` - Health check
- `POST /v1/chat` - Chat with streaming responses

## Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key
- `GATEWAY_TOKEN` - Secret token for frontend authentication
- `ALLOWED_ORIGINS` - Comma-separated allowed origins for CORS
- `LOG_LEVEL` - Logging level (optional, default: INFO)

## Deployment

See RUNBOOK.md for Railway deployment instructions.
# Force redeploy Thu Sep  4 22:57:58 GMT 2025
