# Cursor Prompt: Scaffold Minimal Chatbot (Railway + Vercel)

You are to generate a minimal working chatbot stack. Follow these exact requirements and produce a runnable MVP.

--------------------------------------------------------------------------------
## PROVISIONING MODE (run FIRST; no deploy yet)
Before any coding or deploy steps, output a “Provisioning Required” checklist that includes:
- Accounts & roles needed: Railway (deploy), Vercel (deploy), OpenAI (API access).
- Domains to configure (placeholders acceptable): <API_DOMAIN> (backend), <WEB_DOMAIN> (frontend).
- Environment variables to be provided by the operator (placeholders acceptable).
- Any DNS (CNAME/ALIAS) steps for <API_DOMAIN> and <WEB_DOMAIN>.
Then generate `.env.example` files and a README section titled “How to Provision Railway & Vercel.” Do not proceed to deploy until secrets are supplied.

--------------------------------------------------------------------------------
## TECH STACK

- Backend: Python 3.11 + FastAPI, deployed on Railway.
- Frontend: Single-page HTML + Tailwind CSS (use Tailwind CDN for MVP), deployed on Vercel.
- AI: OpenAI Responses API.
- Domains:
  - <API_DOMAIN> → Railway backend (e.g., api.example.com)
  - <WEB_DOMAIN> → Vercel frontend (e.g., www.example.com)

--------------------------------------------------------------------------------
## REPO LAYOUT (create this structure)

/
├─ backend/                      # FastAPI service
│  ├─ app/                       # source code
│  ├─ tests/                     # (optional) basic smoke test
│  ├─ Dockerfile
│  ├─ requirements.txt
│  ├─ .env.example
│  └─ README.md
├─ frontend/                     # single-page site
│  ├─ public/
│  │  ├─ robots.txt
│  │  ├─ sitemap.xml
│  │  └─ bots.config.json        # UI config: which bots are enabled
│  ├─ index.html
│  ├─ styles.css                 # optional; prefer Tailwind classes inline for MVP
│  └─ README.md
├─ design/
│  ├─ mockups/bot-suite-v1.jpg   # (operator will place)
│  └─ html/current-mockup.html   # (operator will place; preserve structure)
├─ project-brief/
│  ├─ project-brief.rtf
│  ├─ additions-to-deliverables.rtf
│  └─ addendum-design-ux-constraints.rtf
├─ VALIDATION.md                 # acceptance tests (fill with the checklist below)
├─ RUNBOOK.md                    # deploy, rollback, rotate keys, troubleshooting
└─ README.md                     # root overview & architecture

If /design assets or /project-brief files are missing, create placeholders and document where the operator should place the real files.

--------------------------------------------------------------------------------
## BACKEND TASKS (Railway)

1) FastAPI app with two routes:
   - GET /health → returns `{ "status": "ok" }`
   - POST /v1/chat → accepts `{ "messages": [...] }` and proxies to OpenAI Responses API with `stream: true`.

2) Environment variables (all configurable; put in backend/.env.example):
   - OPENAI_API_KEY → secret, never exposed to client
   - GATEWAY_TOKEN → auth secret required by frontend to call backend
   - ALLOWED_ORIGINS → comma-separated allowed origins (e.g., https://www.example.com, https://<preview>.vercel.app)

3) Middleware & policies:
   - CORS restricted to ALLOWED_ORIGINS.
   - Require `Authorization: Bearer ${GATEWAY_TOKEN}` on all POST requests.
   - Logging: request ID, route, status, latency, model ID, token usage (no raw user content).

4) Streaming:
   - Pass through the OpenAI stream to the client unchanged (SSE or chunked text). Ensure first bytes start quickly (no buffering).

5) Error handling & timeouts:
   - Normalize upstream errors to safe JSON (no stack traces, no secrets).
   - Apply a 30–60s request timeout with clear error message.

6) Deployment:
   - Provide a minimal Dockerfile for Railway.
   - Document Railway service creation and env var setup in RUNBOOK.md.
   - Target domain: <API_DOMAIN> (CNAME to Railway), TLS auto-provisioned by platform.

7) Defensive UX contract:
   - Accept a `bot_id` in requests.
   - Reject non-enabled `bot_id`s with a clear 501-style JSON error.

--------------------------------------------------------------------------------
## FRONTEND TASKS (Vercel)

1) Single-page app (`frontend/index.html`) styled with Tailwind (via CDN):
   - Input field + submit button.
   - Output area that prints streamed text in real-time.
   - Visible empty state, streaming state (typing indicator), and error state.

2) Client behaviour:
   - Send POST to `<API_DOMAIN>/v1/chat` with `Authorization: Bearer ${GATEWAY_TOKEN}`.
   - Handle streaming by appending chunks/tokens as they arrive (no “all at once” dump).

3) Accessibility & crawlability:
   - Render meaningful HTML without JS.
   - Provide `robots.txt` and `sitemap.xml` (use <WEB_DOMAIN>).
   - Set sensible meta tags and canonical URL.

4) Deployment:
   - Deploy static site to Vercel; document steps in RUNBOOK.md.
   - Target domain: <WEB_DOMAIN> with TLS.

--------------------------------------------------------------------------------
## DESIGN & UX CONSTRAINTS (MVP SCOPE)

- Use `/design/html/current-mockup.html` and `/design/mockups/bot-suite-v1.jpg` as design constraints.
- Preserve the structure of `current-mockup.html`; reuse class names where possible.
- Only one bot is functional (id: "general") for MVP.
- Display other bots as visible placeholders (disabled) with a small “Coming soon” badge.
- Login/account UI is present visually (as in the mockup) but non-functional; clicking shows a non-blocking “Not available yet” message.
- Disabled bot elements:
  - `aria-disabled="true"`, `tabindex="-1"`, no pointer events.
  - Do not send any network requests when disabled bots are clicked.

--------------------------------------------------------------------------------
## UI CONFIG (so future bots require no redesign)

Create `frontend/public/bots.config.json` with fields per bot:
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
  // more placeholders allowed
]

Frontend reads this file to render bot list and to gate interactivity. Backend rejects disabled `bot_id`s defensively.

--------------------------------------------------------------------------------
## SUCCESS CRITERIA (MUST PASS)

- Visiting <WEB_DOMAIN>, a user enters a prompt and sees tokens stream in real-time.
- Backend proxies to OpenAI with auth & CORS enforced; secrets are never exposed client-side.
- Both services are deployed to their domains with valid TLS.

--------------------------------------------------------------------------------
## STRETCH GOALS (DO NOT IMPLEMENT UNLESS ASKED)

- Redis for basic rate limiting.
- Postgres for conversation history.
- Error tracking with Sentry.
- Additional providers (Gemini, Claude) behind the same gateway.

--------------------------------------------------------------------------------
## ACCEPTANCE TESTS (populate VALIDATION.md with these and provide sample commands)

1) Provisioning & Access
   - Accounts created (Railway, Vercel, OpenAI). Domains reserved.
   - `.env.example` files exist; no secrets in repo.

2) Env Vars (documented & set)
   - Backend: OPENAI_API_KEY, GATEWAY_TOKEN, ALLOWED_ORIGINS, LOG_LEVEL (optional).
   - Frontend: GATEWAY_URL (public), no secrets present.

3) Backend Deploy
   - `GET https://<API_DOMAIN>/health` → `{"status":"ok"}` with 200.

4) Streaming Behaviour (terminal evidence)
   - `curl -N -X POST https://<API_DOMAIN>/v1/chat \
       -H "Authorization: Bearer <GATEWAY_TOKEN>" \
       -H "Content-Type: application/json" \
       -d '{"messages":[{"role":"user","content":"Say hello in one short sentence."}]}'`
   - Output arrives incrementally (not a single flush).

5) Auth & CORS
   - Missing/invalid Authorization → 401/403 with safe JSON.
   - Browser call from <WEB_DOMAIN> succeeds; from non-whitelisted origin fails (CORS).

6) Error Handling & Timeouts
   - Invalid model ID simulates upstream error → clear JSON error (no secrets).
   - Long request hits timeout → clear JSON error.

7) Logging & Telemetry
   - Logs show request ID, route, status, latency, model ID, token usage counts.

8) Frontend Deploy
   - Site live at <WEB_DOMAIN>; chat UI renders; no secrets in bundle.
   - Network tab shows chunked/SSE streaming.

9) Design & Accessibility
   - Layout matches mockup reasonably; placeholders visible and disabled with ARIA.
   - Keyboard-accessible input & submit; visible focus states; AA contrast.

10) Configurability
   - Toggling `enabled` in `bots.config.json` changes interactivity without code changes.
   - Backend rejects disabled `bot_id`s with a clear error.

--------------------------------------------------------------------------------
## RUNBOOK (populate RUNBOOK.md)

- Railway deploy steps, env var setup, and rollback procedure.
- Vercel deploy steps, domain linking, previews, and rollback.
- DNS steps for <API_DOMAIN> and <WEB_DOMAIN>.
- Secret rotation (OPENAI_API_KEY, GATEWAY_TOKEN) and restart impacts.
- Troubleshooting: CORS failures, 401s, streaming not working, DNS not resolved.

--------------------------------------------------------------------------------
## CONSTRAINTS

- Minimal dependencies; no secrets committed; production-safe defaults.
- Do not implement login/auth flows (visual only).
- Keep all OpenAI calls server-side.
- Use the existing mockup HTML structure; document any deviations and why.

END OF SPEC
