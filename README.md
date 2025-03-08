# SMTP Relay with OAuth 2.0 for Outlook

This project provides a dockerized SMTP relay that authenticates with Microsoft Outlook SMTP using OAuth 2.0. It's designed to run in a Docker container on Unraid and is accessible through a Cloudflare Tunnel.

## Features

- OAuth 2.0 authentication with Microsoft Outlook SMTP
- Docker container for easy deployment
- Automatic deployment via GitHub Actions to GHCR
- Cloudflare Tunnel support
- TLS support on port 587
- Compatible with Gmail as a frontend

## Prerequisites

1. Microsoft Azure Account with:
   - Registered application
   - Client ID and Client Secret
2. Docker environment (Unraid)
3. Cloudflare account with Tunnel configured

## Setup

### 1. Azure Application Setup

1. Go to Azure Portal > App Registrations
2. Create a new registration
3. Add API permissions for `https://outlook.office365.com/.default`
4. Create a client secret
5. Note down:
   - Client ID
   - Client Secret
   - Tenant ID (or use 'common')

### 2. Environment Variables

Create a `.env` file with:

```env
GITHUB_USERNAME=your-github-username
CLIENT_ID=your-azure-client-id
CLIENT_SECRET=your-azure-client-secret
USER_EMAIL=your-outlook-email
```

### 3. Docker Deployment

```bash
# Pull and run with docker-compose
docker-compose up -d
```

### 4. Gmail Configuration

1. Go to Gmail > Settings > Accounts & Import
2. Click "Add another email address"
3. Configure SMTP server:
   - SMTP Server: `smtprelay.guggiraid.com`
   - Port: `587`
   - Username: Your Outlook email
   - Password: (any value, not used)
   - Enable TLS: ✓

## API Usage

Send emails via HTTP POST to the root endpoint:

```bash
curl -X POST http://localhost:587 \
  -H "Content-Type: application/json" \
  -d '{
    "to": "recipient@example.com",
    "subject": "Test Email",
    "body": "This is a test email"
  }'
```

## Security

- All communications use TLS
- No credentials stored in container
- OAuth tokens obtained on-demand
- Cloudflare Tunnel provides secure access

## License

MIT License 