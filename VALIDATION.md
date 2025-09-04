# Validation Checklist

This document contains the acceptance tests for the chatbot stack. Run through these tests to verify the system is working correctly.

## 1. Provisioning & Access

- [ ] Railway account created and accessible
- [ ] Vercel account created and accessible  
- [ ] OpenAI account created with API access
- [ ] Domains reserved: `<API_DOMAIN>` and `<WEB_DOMAIN>`
- [ ] `.env.example` files exist in both backend and frontend
- [ ] No secrets committed to repository

## 2. Environment Variables

### Backend (.env)
- [ ] `OPENAI_API_KEY` - Valid OpenAI API key
- [ ] `GATEWAY_TOKEN` - Secure random token
- [ ] `ALLOWED_ORIGINS` - Comma-separated origins including frontend domain
- [ ] `LOG_LEVEL` - Optional, set to INFO

### Frontend Configuration
- [ ] `API_BASE_URL` - Set to backend domain
- [ ] `GATEWAY_TOKEN` - Matches backend token
- [ ] No secrets in frontend code

## 3. Backend Deploy

Test the health endpoint:
```bash
curl https://<API_DOMAIN>/health
```

Expected response:
```json
{"status":"ok"}
```

## 4. Streaming Behaviour

Test streaming chat endpoint:
```bash
curl -N -X POST https://<API_DOMAIN>/v1/chat \
  -H "Authorization: Bearer <GATEWAY_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Say hello in one short sentence."}],"bot_id":"general"}'
```

Expected behavior:
- Response arrives incrementally (not all at once)
- Content is streamed as it's generated
- Final response includes completion signal

## 5. Authentication & CORS

### Test missing authorization:
```bash
curl -X POST https://<API_DOMAIN>/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}]}'
```

Expected: 401 Unauthorized

### Test invalid token:
```bash
curl -X POST https://<API_DOMAIN>/v1/chat \
  -H "Authorization: Bearer invalid_token" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}]}'
```

Expected: 403 Forbidden

### Test CORS from frontend domain:
- [ ] Browser request from `<WEB_DOMAIN>` succeeds
- [ ] Browser request from non-whitelisted origin fails with CORS error

## 6. Error Handling & Timeouts

### Test disabled bot:
```bash
curl -X POST https://<API_DOMAIN>/v1/chat \
  -H "Authorization: Bearer <GATEWAY_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}],"bot_id":"disabled_bot"}'
```

Expected: 501 Not Implemented with clear error message

### Test timeout (if applicable):
- [ ] Long requests timeout with clear error message
- [ ] No stack traces or secrets in error responses

## 7. Logging & Telemetry

Check backend logs for:
- [ ] Request ID in each log entry
- [ ] Route and HTTP method logged
- [ ] Response status code logged
- [ ] Request latency logged
- [ ] Model ID logged (if available)
- [ ] Token usage counts (if available)
- [ ] No raw user content in logs

## 8. Frontend Deploy

- [ ] Site accessible at `<WEB_DOMAIN>`
- [ ] Chat UI renders correctly
- [ ] No secrets visible in browser source
- [ ] Network tab shows streaming requests
- [ ] Bot configuration loads from `/bots.config.json`

## 9. Design & Accessibility

- [ ] Layout matches mockup reasonably well
- [ ] Disabled bots show "Coming soon" badge
- [ ] Disabled bots have `aria-disabled="true"`
- [ ] Disabled bots have `tabindex="-1"`
- [ ] Keyboard navigation works for enabled elements
- [ ] Focus states are visible
- [ ] Color contrast meets AA standards
- [ ] Bot bubble uses preferred color (#F3E1C2)

## 10. Configurability

### Test bot configuration changes:
1. Set `enabled: false` for "general" bot in `bots.config.json`
2. Deploy frontend
3. Verify "general" bot shows as disabled
4. Verify clicking disabled bot shows "not available" message
5. Verify backend rejects disabled bot_id with 501 error

### Test adding new bot:
1. Add new bot to `bots.config.json` with `enabled: false`
2. Deploy frontend
3. Verify new bot appears with "Coming soon" badge
4. Verify new bot is not clickable

## 11. End-to-End Test

Complete user flow:
1. Visit `<WEB_DOMAIN>`
2. Type a message in the input field
3. Press Enter or click Send
4. Verify message appears in chat
5. Verify typing indicator appears
6. Verify bot response streams in real-time
7. Verify response appears in bot bubble with correct styling
8. Verify conversation is saved and appears in sidebar

## Troubleshooting

### Common Issues:

**CORS Errors:**
- Check `ALLOWED_ORIGINS` includes frontend domain
- Verify domain format (no trailing slash)

**401/403 Errors:**
- Verify `GATEWAY_TOKEN` matches between frontend and backend
- Check Authorization header format: `Bearer <token>`

**Streaming Not Working:**
- Check browser network tab for chunked transfer encoding
- Verify backend is using StreamingResponse
- Check for JavaScript errors in console

**Bot Not Responding:**
- Check OpenAI API key is valid
- Verify bot_id is in ENABLED_BOTS list
- Check backend logs for errors

**Frontend Not Loading:**
- Verify Vercel deployment succeeded
- Check domain DNS is pointing to Vercel
- Verify all static files are deployed
