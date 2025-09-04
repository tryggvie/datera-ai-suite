<<<<<<< HEAD
# AI Assistants Suite

A minimal chatbot stack built with FastAPI (Railway) + Vercel + OpenAI.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   OpenAI API    │
│   (Vercel)      │◄──►│   (Railway)     │◄──►│                 │
│   <WEB_DOMAIN>  │    │   <API_DOMAIN>  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

- **Frontend**: Single-page HTML app with Tailwind CSS
- **Backend**: FastAPI with streaming OpenAI integration
- **AI**: OpenAI GPT-3.5-turbo with streaming responses
- **Deployment**: Railway (backend) + Vercel (frontend)

## Quick Start

### Prerequisites

- Railway account
- Vercel account  
- OpenAI API key
- Two domains (or subdomains)

### 1. Provisioning

Before deployment, you need:

1. **Accounts & API Keys:**
   - Railway account for backend deployment
   - Vercel account for frontend deployment
   - OpenAI account with API access

2. **Domains:**
   - `<API_DOMAIN>` for backend (e.g., `api.yourdomain.com`)
   - `<WEB_DOMAIN>` for frontend (e.g., `www.yourdomain.com`)

3. **Environment Variables:**
   - See `backend/.env.example` for backend variables
   - Update `frontend/index.html` with your API domain and gateway token

### 2. Deploy Backend

```bash
cd backend
railway login
railway new
railway up
railway variables set OPENAI_API_KEY=your_key
railway variables set GATEWAY_TOKEN=your_token
railway variables set ALLOWED_ORIGINS=https://www.yourdomain.com
```

### 3. Deploy Frontend

```bash
cd frontend
vercel --prod
```

### 4. Configure DNS

- Point `<API_DOMAIN>` to Railway deployment
- Point `<WEB_DOMAIN>` to Vercel deployment

## Features

- ✅ Real-time streaming chat
- ✅ Multiple bot support (configurable)
- ✅ Responsive design
- ✅ Accessibility features
- ✅ Image attachment support
- ✅ Conversation management
- ✅ Production-ready deployment

## Project Structure

```
/
├── backend/                 # FastAPI service
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py         # Main FastAPI app
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── README.md
├── frontend/               # Static site
│   ├── public/
│   │   ├── bots.config.json
│   │   ├── robots.txt
│   │   └── sitemap.xml
│   ├── index.html          # Main frontend
│   └── README.md
├── design/                 # Design assets
│   ├── mockups/
│   └── html/
├── project-brief/          # Project documentation
├── VALIDATION.md           # Acceptance tests
├── RUNBOOK.md             # Deployment guide
└── README.md              # This file
```

## Configuration

### Bot Configuration

Bots are configured in `frontend/public/bots.config.json`:

```json
[
  {
    "id": "general",
    "name": "General",
    "description": "General-purpose assistant",
    "enabled": true
  },
  {
    "id": "research",
    "name": "Research",
    "description": "Deeper research assistant", 
    "enabled": false
  }
]
```

- `enabled: true` - Bot is functional
- `enabled: false` - Bot shows as "Coming soon"

### Environment Variables

**Backend** (Railway):
- `OPENAI_API_KEY` - Your OpenAI API key
- `GATEWAY_TOKEN` - Secret token for frontend auth
- `ALLOWED_ORIGINS` - Comma-separated allowed origins
- `LOG_LEVEL` - Optional logging level

**Frontend** (in `index.html`):
- `API_BASE_URL` - Backend API domain
- `GATEWAY_TOKEN` - Must match backend token

## API Endpoints

### Backend API

- `GET /health` - Health check
- `POST /v1/chat` - Chat with streaming responses

#### Chat Request Format

```json
{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "bot_id": "general"
}
```

#### Chat Response Format

Streaming response with chunks:
```
data: {"content": "Hello"}
data: {"content": " there!"}
data: {"done": true}
```

## Development

### Local Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your values
uvicorn app.main:app --reload
```

### Local Frontend

```bash
cd frontend
python -m http.server 8000
# Or use any static file server
```

## Testing

Run through the validation checklist in `VALIDATION.md`:

1. Health check endpoint
2. Streaming chat functionality
3. Authentication & CORS
4. Error handling
5. Frontend deployment
6. End-to-end user flow

## Deployment

See `RUNBOOK.md` for detailed deployment instructions:

- Railway backend deployment
- Vercel frontend deployment
- DNS configuration
- Secret rotation
- Monitoring & troubleshooting

## Security

- Gateway token authentication
- CORS protection
- No secrets in frontend code
- HTTPS enforced
- Input validation and sanitization

## Monitoring

- Backend logs via Railway dashboard
- Frontend analytics via Vercel dashboard
- OpenAI usage monitoring
- Error tracking and alerting

## Support

- Check `VALIDATION.md` for troubleshooting
- See `RUNBOOK.md` for operational procedures
- Review logs for error details
- Verify environment variables are set correctly

## License

This project is provided as-is for demonstration purposes.
=======
# datera-ai-suite
>>>>>>> 16f79b4eaefc80109d6ecb7768fb74c0df263d4a
