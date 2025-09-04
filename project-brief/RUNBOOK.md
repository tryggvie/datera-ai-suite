# RUNBOOK — Minimal Chatbot (Railway + Vercel)

This runbook describes how to **deploy**, **roll back**, **configure DNS**, **troubleshoot CORS/streaming**, and **rotate secrets** for the Minimal Chatbot stack.

> **Placeholders**
> - `<API_DOMAIN>` — e.g., `api.example.com`
> - `<WEB_DOMAIN>` — e.g., `www.example.com`
> - `<PROJECT>` — Vercel project slug for previews
> - `<GATEWAY_TOKEN>` — client access token for the gateway (low-privilege)
> - `<OPENAI_API_KEY>` — server-side provider secret (never exposed to clients)

---

## 1) Architecture recap

- **Backend (Gateway):** Python (FastAPI) on **Railway**, exposes:
  - `GET /health`
  - `POST /v1/chat` → proxies to OpenAI **Responses API** with `stream: true`
- **Frontend:** Single-page HTML + **Tailwind** on **Vercel**
- **CORS policy:**
  - **Production (exact):** `https://<WEB_DOMAIN>`
  - **Previews (regex):** `^https://<PROJECT>(-[a-z0-9-]+)?\.vercel\.app$`
  - **Local dev:** `http://localhost:3000` (optional)
- **Tokens & secrets:**
  - `GATEWAY_TOKEN` is a **public client token** used only to gate misuse (rotate regularly).
  - `OPENAI_API_KEY` stays **backend-only** (Railway env).

---

## 2) Provisioning

1. **Accounts**
   - Railway (Editor/Deployer)
   - Vercel (Project Admin)
   - OpenAI (API access)

2. **Domains**
   - `<API_DOMAIN>` → Railway service
   - `<WEB_DOMAIN>` → Vercel project

3. **Environment variables**
   - **Backend (Railway):**
     - `OPENAI_API_KEY`
     - `GATEWAY_TOKEN`
     - `ALLOWED_ORIGINS` (comma-separated exact origins, e.g., `https://<WEB_DOMAIN>,http://localhost:3000`)
     - `ALLOWED_ORIGIN_REGEX` (e.g., `^https://<PROJECT>(-[a-z0-9-]+)?\.vercel\.app$`)
     - `MODEL_ID` (e.g., `gpt-4.1-mini`)
     - `OPENAI_API_BASE` (optional)
   - **Frontend (Vercel):**
     - `GATEWAY_URL` (e.g., `https://<API_DOMAIN>`)

> **Do not proceed to deploy** until the above are set. See `VALIDATION.md` §0–1 for checks.

---

## 3) DNS setup

### 3.1 Backend — `<API_DOMAIN>` → Railway
1. In your DNS provider, create a **CNAME** record:
   - Name/Host: `<API_DOMAIN>`
   - Value/Target: the Railway-provided hostname for your service
   - TTL: 300s (or project default)
2. Wait for propagation.
3. Verify TLS:
   ```bash
   curl -I https://<API_DOMAIN>
   ```

### 3.2 Frontend — `<WEB_DOMAIN>` → Vercel
1. Add the custom domain in Vercel project settings.
2. Follow Vercel’s DNS instructions (often **CNAME** to `cname.vercel-dns.com`).
3. Verify TLS:
   ```bash
   curl -I https://<WEB_DOMAIN>
   ```

---

## 4) Deploy

### 4.1 Backend (Railway)
- Ensure `backend/` contains `Dockerfile`, `requirements.txt`, app code.
- In Railway:
  1. New Project → Deploy from GitHub or CLI.
  2. Set **Environment Variables** listed in §2.
  3. Deploy. Confirm logs show server listening.
  4. Health check:
     ```bash
     curl https://<API_DOMAIN>/health
     ```

### 4.2 Frontend (Vercel)
- Connect `frontend/` to Vercel.
- Set **Environment Variables**:
  - `GATEWAY_URL=https://<API_DOMAIN>`
- Deploy. Confirm site loads at `<WEB_DOMAIN>`.

---

## 5) Rollback

### 5.1 Backend (Railway)
- Go to the service **Deployments** tab → select previous successful deployment → **Rollback/Promote**.
- Verify health:
  ```bash
  curl https://<API_DOMAIN>/health
  ```

### 5.2 Frontend (Vercel)
- In **Deployments**, pick a previous build → **Promote to Production**.
- Validate:
  ```bash
  curl -I https://<WEB_DOMAIN>
  ```

> Keep at least 1 prior deployment available on both platforms for quick recovery.

---

## 6) CORS troubleshooting

### 6.1 Check production allow
```bash
curl -i -X OPTIONS https://<API_DOMAIN>/v1/chat   -H "Origin: https://<WEB_DOMAIN>"   -H "Access-Control-Request-Method: POST"
```
Expected: `Access-Control-Allow-Origin: https://<WEB_DOMAIN>`

### 6.2 Block non-whitelisted origin
```bash
curl -i -X OPTIONS https://<API_DOMAIN>/v1/chat   -H "Origin: https://evil.example"   -H "Access-Control-Request-Method: POST"
```
Expected: no permissive CORS headers (and/or 403).

### 6.3 Allow previews (regex)
```bash
curl -i -X OPTIONS https://<API_DOMAIN>/v1/chat   -H "Origin: https://<PROJECT>-abc123.vercel.app"   -H "Access-Control-Request-Method: POST"
```
Expected: allowed.

**If failing:** verify `ALLOWED_ORIGINS` and `ALLOWED_ORIGIN_REGEX` envs; restart backend.

---

## 7) Streaming/SSE troubleshooting

**Symptom:** response arrives only after completion (no incremental tokens).  
**Checks:**
1. Use `-N` to disable curl buffering:
   ```bash
   curl -N -X POST https://<API_DOMAIN>/v1/chat      -H "Authorization: Bearer <GATEWAY_TOKEN>"      -H "Content-Type: application/json"      -H "Origin: https://<WEB_DOMAIN>"      -d '{"messages":[{"role":"user","content":"Say hello in one short sentence."}]}'
   ```
2. Ensure upstream call requests `stream: true`.
3. Confirm no reverse-proxy buffering between client and Railway.
4. Verify response headers include `Content-Type: text/event-stream` (or chunked transfer).

---

## 8) Secret & token rotation

### 8.1 Rotate `OPENAI_API_KEY` (backend-only secret)
1. Add **new key** in Railway env as `OPENAI_API_KEY` (overwrite value).
2. Redeploy backend.
3. Validate `/health` and a test chat.
4. Remove old key from any out-of-band storage.

### 8.2 Rotate `GATEWAY_TOKEN` (client access token)
> This token is visible to clients (not a secret). Rotate to reduce misuse.

Two safe options:
- **Coordinated cutover (simple)**  
  1. Update `GATEWAY_TOKEN` in Railway.  
  2. Update `GATEWAY_URL` or embed new token in frontend as needed (per implementation).  
  3. Deploy frontend immediately.  
  4. Verify new header is sent and accepted.

- **Dual-accept window (preferred if implemented)**  
  1. Configure backend to accept **old + new** tokens for a brief window.  
  2. Update frontend to send the **new** token.  
  3. After 15–30 minutes, disable the old token server-side.

**Audit:** check logs for rejected tokens after rotation.

---

## 9) Performance checks (baseline)

Targets (from brief):
- **First byte ≤ 2s cold** on trivial prompts.
- **P95 ≤ 5s** end-to-end on short prompts.

Quick test:
- Send 10 short prompts via `/v1/chat` and capture start/end times in a spreadsheet or simple script.
- Investigate sustained slow responses (provider latency, network, cold starts).

---

## 10) Logging & cost visibility

- **Gateway logs** should include: request ID, route, status, latency, `MODEL_ID`, token counts (no raw content).
- **OpenAI usage**: review the provider dashboard for daily token consumption & costs.
- **Alerting (optional)**: set budget alerts or daily usage reports via your platform of choice.

---

## 11) Known error messages (user-friendly copy)

- **Auth missing/invalid:** “Cannot reach the chat service (authorisation required).”
- **CORS blocked:** “This environment is not authorised to use the chat service.”
- **Timeout:** “The model is taking too long—please try again.”
- **Generic:** “Something went wrong. Please try again.”

Ensure API returns corresponding JSON errors without stack traces or secrets.

---

## 12) Local development

### Backend (Railway-like locally)
```bash
# In backend/
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=...
export GATEWAY_TOKEN=dev-token
export ALLOWED_ORIGINS=http://localhost:3000
export MODEL_ID=gpt-4.1-mini
uvicorn app.main:app --port 8000 --reload
```

### Frontend (local preview)
- Serve `frontend/` via any static server or `vercel dev`.
- Set `GATEWAY_URL=http://localhost:8000` in local env.
- Ensure CORS allows `http://localhost:3000`.

---

## 13) Incident response (quick checklist)

1. **Triage:** Is outage frontend-only, backend-only, or provider-side?
2. **Status pages:** Check Vercel, Railway, and OpenAI status dashboards.
3. **Rollback:** Promote last known-good deployments (see §5).
4. **Comms:** Post an internal status note with ETA and scope.
5. **Postmortem:** Capture cause, fix, and prevention steps.

---

## 14) Appendices

### A. Handy curl commands
```bash
# Health
curl https://<API_DOMAIN>/health

# Auth’d chat (stream)
curl -N -X POST https://<API_DOMAIN>/v1/chat   -H "Authorization: Bearer <GATEWAY_TOKEN>"   -H "Content-Type: application/json"   -H "Origin: https://<WEB_DOMAIN>"   -d '{"messages":[{"role":"user","content":"Say hello in one short sentence."}]}'
```

### B. Quick checklist before go-live
- Env vars set on both platforms
- DNS points to correct targets; TLS valid
- CORS verified for prod + preview + localhost
- Streaming verified (first byte in ≤ 2s on trivial prompt)
- Error messages render correctly in UI
- `VALIDATION.md` completed with evidence
