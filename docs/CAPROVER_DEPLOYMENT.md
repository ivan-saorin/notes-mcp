# CapRover Deployment Guide

This guide provides detailed instructions for deploying your MCP server to CapRover.

## Prerequisites

- CapRover instance (v1.10.0+)
- GitHub repository with your MCP server code
- Domain name (optional but recommended)
- SSL certificate (CapRover can auto-generate with Let's Encrypt)

## Step 1: Prepare Your Repository

### 1.1 Verify Dockerfile Location

Ensure your Dockerfile is at exactly this path:
```
deploy/caprover/Dockerfile
```

CapRover specifically looks for this path when building from GitHub.

### 1.2 Review Dockerfile

Your Dockerfile should be optimized for production:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY run_server.py .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Run server
CMD ["python", "run_server.py"]
```

## Step 2: Create GitHub Personal Access Token

### 2.1 Generate Token

1. Go to GitHub → Settings → Developer settings
2. Click "Personal access tokens" → "Tokens (classic)"
3. Click "Generate new token (classic)"
4. Configure token:
   - **Note**: `CapRover Deployment for MCP Server`
   - **Expiration**: Choose appropriate duration
   - **Scopes**:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `admin:repo_hook` (Full control of repository hooks)
5. Click "Generate token"
6. **COPY THE TOKEN IMMEDIATELY** - you won't see it again!

### 2.2 Store Token Securely

Save your token in a password manager. You'll need it for CapRover configuration.

## Step 3: Configure CapRover App

### 3.1 Create New App

1. Log into CapRover dashboard
2. Navigate to "Apps"
3. Click "Create A New App"
4. Enter app name (e.g., `mcp-server`)
   - Use lowercase letters, numbers, and hyphens only
   - This will become your subdomain: `mcp-server.your-domain.com`
5. Click "Create New App"

### 3.2 Configure GitHub Deployment

1. In your app's page, click on "Deployment" tab
2. Scroll to "Method 3: Deploy from GitHub/GitLab/BitBucket"
3. Fill in the configuration:

   **Repository**: 
   ```
   https://github.com/YOUR_USERNAME/your-mcp-server
   ```
   
   **Branch**: 
   ```
   main
   ```
   (or `master`, depending on your default branch)
   
   **Username**: 
   ```
   YOUR_GITHUB_EMAIL@example.com
   ```
   
   **Password**: 
   ```
   [PASTE YOUR PERSONAL ACCESS TOKEN HERE]
   ```

4. Click "Save & Update"
5. **IMPORTANT**: Copy the webhook URL that appears:
   ```
   https://captain.your-domain.com/api/v2/user/apps/webhooks/triggerbuild?namespace=captain&token=XXXX
   ```

### 3.3 Test Manual Deployment

1. Click "Force Build"
2. Watch the deployment logs
3. If successful, you'll see "Build successfully completed!"

Common issues:
- **"Dockerfile not found"**: Ensure it's at `deploy/caprover/Dockerfile`
- **"Authentication failed"**: Check your PAT has correct permissions
- **"Build failed"**: Check logs for Python/dependency errors

## Step 4: Configure GitHub Webhook

### 4.1 Add Webhook to Repository

1. Go to your GitHub repository
2. Click Settings → Webhooks
3. Click "Add webhook"
4. Configure webhook:

   **Payload URL**: 
   ```
   [PASTE THE CAPROVER WEBHOOK URL HERE]
   ```
   
   **Content type**: 
   ```
   application/json
   ```
   
   **Secret**: 
   ```
   [Leave empty unless you configured one in CapRover]
   ```
   
   **Which events would you like to trigger this webhook?**
   - Select "Just the push event"
   
   **Active**: 
   - ✅ Check this box

5. Click "Add webhook"

### 4.2 Test Webhook

1. Make a small change to your repository:
   ```bash
   echo "# Deployment test" >> README.md
   git add README.md
   git commit -m "Test CapRover webhook"
   git push origin main
   ```

2. Check webhook delivery:
   - In GitHub: Settings → Webhooks → Click your webhook → Recent Deliveries
   - Look for green checkmark ✓
   - If red X, click to see error details

3. Check CapRover:
   - Go to your app's Deployment logs
   - You should see the build triggered automatically

## Step 5: Configure App Settings

### 5.1 Environment Variables

1. In CapRover app settings → "App Configs" tab
2. Scroll to "Environmental Variables"
3. Add your variables:
   ```
   PORT=8000
   HOST=0.0.0.0
   LOG_LEVEL=INFO
   # Add any API keys or secrets here
   YOUR_API_KEY=your_actual_key
   ```
4. Click "Save & Update"

### 5.2 Persistent Storage (if needed)

If your MCP server needs persistent storage:

1. Go to "App Configs" tab
2. Scroll to "Persistent Directories"
3. Add directory:
   - **Path**: `/app/data`
   - **Label**: `mcp-data`
4. Click "Save & Update"

### 5.3 Resource Limits

1. Go to "App Configs" tab
2. Set resource limits:
   - **Instance Count**: Start with 1
   - **CPU**: 0.5 (500m)
   - **Memory**: 512 (MB)
3. Adjust based on your needs

## Step 6: Configure Domain and SSL

### 6.1 Add Custom Domain

1. Go to "HTTP Settings" tab
2. In "Connecting Custom Domain" section:
   - Enter your domain: `mcp.your-domain.com`
   - Click "Connect New Domain"

3. Configure DNS:
   - Add CNAME record pointing to `captain.your-caprover-domain.com`
   - Or A record pointing to your server IP

### 6.2 Enable HTTPS

1. After domain is verified (green checkmark)
2. Click "Enable HTTPS"
3. Enter email for Let's Encrypt
4. Click "Enable HTTPS"
5. Wait for certificate generation

### 6.3 Force HTTPS

1. After SSL is enabled
2. Check "Force HTTPS by redirecting all HTTP traffic to HTTPS"
3. Click "Save & Update"

## Step 7: Health Monitoring

### 7.1 Configure Health Check

CapRover automatically monitors your app. Ensure your health endpoint works:

```bash
curl https://mcp.your-domain.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Atlas Remote MCP",
  "version": "2.0.0"
}
```

### 7.2 Setup Monitoring

1. Go to "Monitoring" tab
2. View metrics:
   - CPU usage
   - Memory usage
   - Network I/O
   - Disk usage

### 7.3 Configure Alerts (Optional)

1. Install NetData on your CapRover server
2. Configure alerts for:
   - High CPU usage
   - Memory leaks
   - App crashes
   - SSL certificate expiration

## Step 8: Testing Your Deployment

### 8.1 Test with curl

```bash
# Health check
curl https://mcp.your-domain.com/health

# List tools
curl -X POST https://mcp.your-domain.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

### 8.2 Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector --url https://mcp.your-domain.com/mcp
```

### 8.3 Load Testing

```bash
# Install hey
go install github.com/rakyll/hey@latest

# Run load test
hey -n 1000 -c 10 https://mcp.your-domain.com/health
```

## Troubleshooting

### Build Failures

**Issue**: "Cannot find Dockerfile"
```
Solution: Ensure Dockerfile is at deploy/caprover/Dockerfile
```

**Issue**: "Module not found"
```
Solution: Check all dependencies are in requirements.txt
```

**Issue**: "Permission denied"
```
Solution: Ensure Dockerfile creates and uses non-root user
```

### Runtime Errors

**Issue**: "Connection refused"
```
Solutions:
1. Check app is running on port 8000
2. Verify HOST is set to 0.0.0.0
3. Check CapRover app logs
```

**Issue**: "502 Bad Gateway"
```
Solutions:
1. App may be starting up - wait 30 seconds
2. Check health endpoint is working
3. Verify port configuration
```

**Issue**: "SSL certificate error"
```
Solutions:
1. Wait for Let's Encrypt to generate certificate
2. Ensure domain DNS is properly configured
3. Check CapRover SSL settings
```

### Webhook Issues

**Issue**: "Webhook not triggering builds"
```
Solutions:
1. Verify webhook URL is correct
2. Check PAT has repo and admin:repo_hook permissions
3. Review GitHub webhook delivery history
4. Ensure branch name matches configuration
```

**Issue**: "Authentication failed"
```
Solutions:
1. Regenerate PAT with correct permissions
2. Update CapRover with new token
3. Verify GitHub username is correct
```

## Advanced Configuration

### Multi-Instance Deployment

For high availability:

1. Go to "App Configs" → "Instance Count"
2. Increase to 2 or more
3. CapRover will load balance automatically

### Custom Nginx Configuration

1. Go to "HTTP Settings" tab
2. Edit "Custom Nginx Config":

```nginx
client_max_body_size 50m;
proxy_read_timeout 300s;
proxy_connect_timeout 75s;

location /mcp {
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### Database Connection

If using external database:

1. Add connection string as environment variable
2. Ensure your CapRover server can reach the database
3. Consider using CapRover's one-click database apps

### Backup Strategy

1. **Code**: Already in GitHub
2. **Data**: Use persistent directories
3. **Configuration**: Export environment variables
4. **Schedule**: Set up automated backups

```bash
# Backup script example
#!/bin/bash
docker exec -it $(docker ps -qf "name=srv-captain--mcp-server") \
  tar -czf /backup/mcp-data-$(date +%Y%m%d).tar.gz /app/data
```

## Security Best Practices

1. **Use HTTPS always** - Never transmit data over HTTP
2. **Rotate tokens regularly** - Update PAT every 90 days
3. **Limit permissions** - Only grant necessary scopes
4. **Monitor logs** - Check for suspicious activity
5. **Update dependencies** - Keep Python packages current
6. **Use secrets management** - Never commit secrets to GitHub
7. **Implement rate limiting** - Prevent abuse
8. **Add authentication** - Protect sensitive tools

## Scaling Considerations

As your MCP server grows:

1. **Horizontal scaling**: Increase instance count
2. **Vertical scaling**: Increase CPU/memory limits
3. **Caching**: Implement Redis for frequent operations
4. **CDN**: Use Cloudflare for static assets
5. **Database**: Move from SQLite to PostgreSQL
6. **Monitoring**: Add APM tools like New Relic
7. **Logging**: Centralize with ELK stack

## Maintenance

### Regular Tasks

- **Weekly**: Check logs for errors
- **Monthly**: Review resource usage
- **Quarterly**: Update dependencies
- **Yearly**: Rotate all secrets

### Update Process

1. Test changes locally
2. Push to development branch
3. Test on staging CapRover app
4. Merge to main branch
5. Automatic deployment via webhook
6. Verify production deployment

## Getting Help

- **CapRover Documentation**: https://caprover.com/docs
- **CapRover Slack**: https://caprover.com/community
- **GitHub Issues**: Report bugs in your repository
- **MCP Community**: https://modelcontextprotocol.io/community

---

Congratulations! Your MCP server is now deployed and accessible from anywhere! 🎉
