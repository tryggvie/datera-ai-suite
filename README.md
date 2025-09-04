# Frontend

Single-page chatbot frontend deployed on Vercel.

## Features

- Real-time streaming chat interface
- Multiple bot support (configurable via bots.config.json)
- Responsive design with Tailwind CSS
- Accessibility features (ARIA labels, keyboard navigation)
- Image attachment support
- Conversation management

## Configuration

Update the following in `index.html`:

1. **API_BASE_URL**: Replace with your actual API domain
2. **GATEWAY_TOKEN**: Replace with your actual gateway token

## Bot Configuration

Bots are configured in `public/bots.config.json`:

```json
[
  {
    "id": "general",
    "name": "General",
    "description": "General-purpose assistant",
    "enabled": true
  }
]
```

- `enabled: true` - Bot is functional and clickable
- `enabled: false` - Bot shows as "Coming soon" and is disabled

## Deployment

See RUNBOOK.md for Vercel deployment instructions.

## Local Development

1. Serve the files using any static file server:
```bash
# Using Python
python -m http.server 8000

# Using Node.js
npx serve .

# Using PHP
php -S localhost:8000
```

2. Open http://localhost:8000 in your browser
