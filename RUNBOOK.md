# Runbook

This document contains deployment, maintenance, and troubleshooting procedures for the chatbot stack.

## Architecture Overview

- **Backend**: FastAPI on Railway (`<API_DOMAIN>`)
- **Frontend**: Static site on Vercel (`<WEB_DOMAIN>`)
- **AI Provider**: OpenAI API
- **Authentication**: Gateway token system

## Railway Backend Deployment

### Initial Setup

1. **Create Railway Project:**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login to Railway
   railway login
   
   # Create new project
   railway new
   ```

2. **Deploy Backend:**
   ```bash
   cd backend
   railway up
   ```

3. **Set Environment Variables:**
   ```bash
   railway variables set OPENAI_API_KEY=your_openai_api_key
   railway variables set GATEWAY_TOKEN=your_secure_gateway_token
   railway variables set ALLOWED_ORIGINS=https://www.yourdomain.com,https://your-preview.vercel.app
   railway variables set LOG_LEVEL=INFO
   ```

4. **Get Deployment URL:**
   ```bash
   railway domain
   ```

### Backend Rollback

1. **List Deployments:**
   ```bash
   railway deployments
   ```

2. **Rollback to Previous:**
   ```bash
   railway rollback <deployment-id>
   ```

### Backend Monitoring

1. **View Logs:**
   ```bash
   railway logs
   ```

2. **View Metrics:**
   - Visit Railway dashboard
   - Check CPU, memory, and request metrics

## Vercel Frontend Deployment

### Initial Setup

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Deploy Frontend:**
   ```bash
   cd frontend
   vercel --prod
   ```

3. **Configure Domain:**
   - Go to Vercel dashboard
   - Select your project
   - Go to Settings > Domains
   - Add your custom domain `<WEB_DOMAIN>`

### Frontend Rollback

1. **List Deployments:**
   ```bash
   vercel ls
   ```

2. **Rollback to Previous:**
   ```bash
   vercel rollback <deployment-url>
   ```

### Frontend Monitoring

1. **View Analytics:**
   - Visit Vercel dashboard
   - Check Analytics tab for traffic and performance

2. **View Function Logs:**
   - Go to Functions tab in Vercel dashboard
   - View real-time logs

## DNS Configuration

### Backend Domain (`<API_DOMAIN>`)

1. **Get Railway Domain:**
   ```bash
   railway domain
   ```

2. **Configure DNS:**
   - Add CNAME record: `api` → `your-app.railway.app`
   - Or use Railway's custom domain feature

### Frontend Domain (`<WEB_DOMAIN>`)

1. **Get Vercel Domain:**
   - Check Vercel dashboard for assigned domain

2. **Configure DNS:**
   - Add CNAME record: `www` → `cname.vercel-dns.com`
   - Or use A record: `www` → Vercel IP addresses

## Secret Rotation

### Rotate Gateway Token

1. **Generate New Token:**
   ```bash
   # Generate secure random token
   openssl rand -hex 32
   ```

2. **Update Backend:**
   ```bash
   railway variables set GATEWAY_TOKEN=new_token
   ```

3. **Update Frontend:**
   - Update `GATEWAY_TOKEN` in `index.html`
   - Redeploy frontend

4. **Restart Backend:**
   ```bash
   railway restart
   ```

### Rotate OpenAI API Key

1. **Generate New Key:**
   - Go to OpenAI dashboard
   - Create new API key
   - Delete old key after confirming new one works

2. **Update Backend:**
   ```bash
   railway variables set OPENAI_API_KEY=new_api_key
   ```

3. **Restart Backend:**
   ```bash
   railway restart
   ```

## Troubleshooting

### Backend Issues

#### Service Not Starting
```bash
# Check logs
railway logs

# Common issues:
# - Missing environment variables
# - Invalid OpenAI API key
# - Port binding issues
```

#### CORS Errors
1. Check `ALLOWED_ORIGINS` includes frontend domain
2. Verify domain format (no trailing slash)
3. Check for typos in domain names

#### 401/403 Errors
1. Verify `GATEWAY_TOKEN` matches between frontend and backend
2. Check Authorization header format: `Bearer <token>`
3. Ensure token is not URL-encoded

#### Streaming Not Working
1. Check browser network tab for chunked transfer encoding
2. Verify backend is using `StreamingResponse`
3. Check for JavaScript errors in console
4. Verify OpenAI API key has streaming permissions

### Frontend Issues

#### Site Not Loading
1. Check Vercel deployment status
2. Verify domain DNS is pointing to Vercel
3. Check for build errors in Vercel logs

#### API Calls Failing
1. Verify `API_BASE_URL` is correct
2. Check browser console for CORS errors
3. Verify `GATEWAY_TOKEN` matches backend

#### Bot Configuration Not Loading
1. Check `/bots.config.json` is accessible
2. Verify JSON syntax is valid
3. Check browser network tab for 404 errors

### OpenAI Issues

#### API Key Invalid
1. Verify key is correct in Railway variables
2. Check key has proper permissions
3. Verify account has sufficient credits

#### Rate Limiting
1. Check OpenAI usage dashboard
2. Implement exponential backoff
3. Consider upgrading OpenAI plan

#### Model Errors
1. Check model name is correct (`gpt-3.5-turbo`)
2. Verify model is available in your region
3. Check for model-specific errors in logs

## Monitoring & Alerting

### Key Metrics to Monitor

1. **Backend:**
   - Response time
   - Error rate
   - Memory usage
   - Request volume

2. **Frontend:**
   - Page load time
   - API call success rate
   - User engagement metrics

3. **OpenAI:**
   - API usage
   - Rate limit hits
   - Error responses

### Recommended Alerts

1. **High Error Rate:** >5% errors in 5 minutes
2. **High Response Time:** >10s average response time
3. **Memory Usage:** >80% memory usage
4. **API Failures:** OpenAI API errors

## Backup & Recovery

### Backend Data
- Railway handles automatic backups
- No persistent data to backup (stateless service)

### Frontend Data
- Vercel handles automatic backups
- Source code is in Git repository

### Configuration Backup
- Environment variables are stored in Railway/Vercel
- Bot configuration is in Git repository
- DNS configuration should be documented

## Security Considerations

### Secrets Management
- Never commit secrets to Git
- Use environment variables for all secrets
- Rotate secrets regularly
- Use strong, random tokens

### API Security
- Gateway token provides basic authentication
- CORS restricts access to allowed origins
- No user authentication (by design for MVP)

### Network Security
- All traffic uses HTTPS (TLS)
- Railway and Vercel handle TLS certificates
- No direct database access (stateless)

## Performance Optimization

### Backend
- Use connection pooling for OpenAI API
- Implement request caching if needed
- Monitor memory usage and scale if necessary

### Frontend
- Use CDN for static assets (Vercel handles this)
- Minimize JavaScript bundle size
- Implement proper caching headers

### OpenAI
- Use appropriate model for use case
- Implement request batching if needed
- Monitor token usage and costs
