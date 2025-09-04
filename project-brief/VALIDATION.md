# VALIDATION & ACCEPTANCE TESTS

**Goal:** Verify the Minimal Chatbot (Railway + Vercel) meets the brief.  
**How to use:** Work top-to-bottom. For each item, tick ✅/❌ and attach **evidence** (URL, curl output, screenshots, log excerpts).

> **Placeholders used below**
> - `<API_DOMAIN>` (e.g., `api.example.com`)
> - `<WEB_DOMAIN>` (e.g., `www.example.com`)
> - `<PROJECT>` = Vercel project slug (for preview subdomains)
> - `<GATEWAY_TOKEN>` = backend auth token

---

## 0) Provisioning & Structure

- [ ] **Accounts**: Railway, Vercel, OpenAI exist with deploy/API access.  
  **Evidence:** screenshots of project dashboards.
- [ ] **Repo layout** matches spec (`backend/`, `frontend/`, `design/`, `project-brief/`, `VALIDATION.md`, `RUNBOOK.md`).  
  **Evidence:** repo tree screenshot or `ls -R` snippet.
- [ ] **Design assets** present at canonical paths: `/design/html/current-mockup.html`, `/design/mockups/bot-suite-v1.png`.  
  **Evidence:** file listing or screenshot.
- [ ] **Env samples** exist: `backend/.env.example`, `frontend/.env.example`.  
  **Evidence:** file snippets (variable names only).

---

## 1) Environment Variables (documented & set)

**Backend (`backend/.env.example` must include):**
- [ ] `OPENAI_API_KEY`
- [ ] `GATEWAY_TOKEN`
- [ ] `ALLOWED_ORIGINS` (e.g., `https://<WEB_DOMAIN>,http://localhost:3000`)
- [ ] `ALLOWED_ORIGIN_REGEX` (e.g., `^https://<PROJECT>(-[a-z0-9-]+)?\.vercel\.app$`)
- [ ] `MODEL_ID` (not hard-coded)
- [ ] `OPENAI_API_BASE` (optional)

**Frontend (`frontend/.env.example`):**
- [ ] `GATEWAY_URL` (public)

**Evidence:** screenshots/snippets of `.env.example` and platform env pages (secrets redacted).

---

## 2) Backend Deploy (Railway)

- [ ] **Health:** `GET https://<API_DOMAIN>/health` → `{"status":"ok"}` (200).  
  **Evidence:** curl output.

- [ ] **TLS** valid on `<API_DOMAIN>`.  
  **Evidence:**
  ```bash
  curl -I https://<API_DOMAIN>
  ```

- [ ] **RUNBOOK.md** documents Railway deploy & rollback steps.  
  **Evidence:** link or screenshot.

---

## 3) Auth & CORS

- [ ] **No auth** → 401/403 with safe JSON (no stack traces).  
  **Evidence:**
  ```bash
  curl -i -X POST https://<API_DOMAIN>/v1/chat     -H "Content-Type: application/json"     -d '{"messages":[{"role":"user","content":"test"}]}'
  ```

- [ ] **Invalid token** → 401/403 with safe JSON.  
  **Evidence:** same as above with bad `Authorization`.

- [ ] **CORS (production allowed)**
  ```bash
  curl -i -X OPTIONS https://<API_DOMAIN>/v1/chat     -H "Origin: https://<WEB_DOMAIN>"     -H "Access-Control-Request-Method: POST"
  ```
  Expect `Access-Control-Allow-Origin: https://<WEB_DOMAIN>`.

- [ ] **CORS (non-whitelisted blocked)**
  ```bash
  curl -i -X OPTIONS https://<API_DOMAIN>/v1/chat     -H "Origin: https://evil.example"     -H "Access-Control-Request-Method: POST"
  ```
  Expect **no** permissive CORS headers (and/or 403).

- [ ] **CORS (preview allowed via regex)**
  ```bash
  curl -i -X OPTIONS https://<API_DOMAIN>/v1/chat     -H "Origin: https://<PROJECT>-abc123.vercel.app"     -H "Access-Control-Request-Method: POST"
  ```
  Expect allowed.

**Evidence:** raw `curl -i` outputs for all three.

---

## 4) Streaming Behaviour (API)

- [ ] **Tokens stream incrementally** (not one big flush).  
  **Evidence:**
  ```bash
  curl -N -X POST https://<API_DOMAIN>/v1/chat     -H "Authorization: Bearer <GATEWAY_TOKEN>"     -H "Content-Type: application/json"     -H "Origin: https://<WEB_DOMAIN>"     -d '{"messages":[{"role":"user","content":"Say hello in one short sentence."}]}'
  ```
  Attach a short screen recording or paste showing incremental chunks.

---

## 5) Error Handling & Timeouts

- [ ] **Upstream error normalized** (use invalid model ID) → clear JSON (no secrets/stack).  
  **Evidence:** curl output.

- [ ] **Timeout** (30–60s) produces clear JSON error.  
  **Evidence:** curl output or logs showing timeout handling.

---

## 6) Logging & Telemetry (no PII)

- [ ] Request logs include: request ID, route, status, latency, **model ID**, token counts (prompt/response if available).  
  **Evidence:** log excerpts (mask IDs if needed).

- [ ] **No raw prompts** stored or logged.  
  **Evidence:** logging policy snippet or grep results.

---

## 7) Frontend Deploy (Vercel)

- [ ] Site live at `https://<WEB_DOMAIN>`; loads successfully.  
  **Evidence:** URL + screenshot.

- [ ] **DNS/TLS proof**  
  **Evidence:**
  ```bash
  curl -I https://<WEB_DOMAIN>
  ```

- [ ] Frontend uses `GATEWAY_URL` to call backend; **no secrets** in client bundle.  
  **Evidence:** DevTools Network → request URL, headers (no API key), and bundle search for “OPENAI”/key patterns.

---

## 8) End-to-End Streaming (Browser)

- [ ] Enter a prompt on `<WEB_DOMAIN>` and observe **streaming** tokens (not a single final blob).  
  **Evidence:** short screen recording.

- [ ] DevTools Network shows a streaming (SSE/chunked) response for `/v1/chat`.  
  **Evidence:** screenshot of the streaming request.

---

## 9) Design & UX Constraints

- [ ] UI matches mockup structure from `/design/html/current-mockup.html` (no heavy redesign).  
  **Evidence:** side-by-side screenshot.

- [ ] **One active bot only**; other bots visible as placeholders with **“Coming soon”** badge/tooltip.  
  **Evidence:** screenshot(s).

- [ ] **Disabled bots do not trigger network calls**; clicking shows a non-blocking message.  
  **Evidence:** DevTools Network (no request) + UI screenshot.

- [ ] **Login UI visible but non-functional**; clicking shows “Not enabled yet”.  
  **Evidence:** screenshot.

- [ ] **States implemented**: empty, streaming (typing indicator stops on completion/error), error messages.  
  **Evidence:** screenshots/video.

- [ ] **Accessibility**:  
  - Disabled bot controls have `aria-disabled="true"` and `tabindex="-1"`.  
  - Keyboard can focus input and send; visible focus state.  
  - Text contrast ≥ AA.  
  **Evidence:** DOM inspection screenshots + a11y report or notes.

---

## 10) Configurability & Bot Gating

- [ ] `frontend/public/bots.config.json` exists; frontend **reads at runtime** (no rebuild needed to toggle).  
  **Evidence:** file snippet + demonstration of toggling `enabled`.

- [ ] Backend **rejects disabled `bot_id`s** with clear JSON (e.g., 501).  
  **Evidence:** curl POST with disabled `bot_id`.

- [ ] `MODEL_ID` is configurable (env or config), not hard-coded.  
  **Evidence:** show env and logs including model ID.

---

## 11) Performance Baselines

Run 10 short prompts and check timing (cold + warm):

- [ ] **First byte ≤ 2s cold** (first request after deploy).  
- [ ] **P95 ≤ 5s** end-to-end for short prompts.

**Evidence:** timing screenshots (DevTools waterfall) or a simple timing log table.

---

## 12) Security Hygiene

- [ ] No secrets in repo or client bundle.  
  **Evidence:**
  ```bash
  grep -R "OPENAI_API_KEY" -n .
  grep -R "<your_key_prefix_if_any>" -n frontend
  ```
  (Expect **no matches** outside backend env references.)

- [ ] **CORS policy** matches brief: production exact origin; previews via `ALLOWED_ORIGIN_REGEX`; `localhost:3000` for local dev only.  
  **Evidence:** config screenshots/snippets.

---

## 13) Optional (Rate limiting, if implemented)

- [ ] Rapid 10–20 requests trigger 429 with retry advice; normal traffic passes.  
  **Evidence:** curl loop output + log snippet.

---

## 14) Sign-off

- [ ] All required checks passed.  
  **Sign-off name & date:**  
  **Notes / deviations approved by:**

---

### Appendix A — Handy curl snippets

**Auth’d chat (stream):**
```bash
curl -N -X POST https://<API_DOMAIN>/v1/chat   -H "Authorization: Bearer <GATEWAY_TOKEN>"   -H "Content-Type: application/json"   -H "Origin: https://<WEB_DOMAIN>"   -d '{"messages":[{"role":"user","content":"Say hello in one short sentence."}]}'
```

**CORS preflight (allowed):**
```bash
curl -i -X OPTIONS https://<API_DOMAIN>/v1/chat   -H "Origin: https://<WEB_DOMAIN>"   -H "Access-Control-Request-Method: POST"
```

**CORS preflight (blocked):**
```bash
curl -i -X OPTIONS https://<API_DOMAIN>/v1/chat   -H "Origin: https://evil.example"   -H "Access-Control-Request-Method: POST"
```
