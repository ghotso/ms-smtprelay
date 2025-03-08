import os
import logging
from flask import Flask, request
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import msal
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('smtp_relay')

app = Flask(__name__)

# Configuration
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
TENANT_ID = os.environ.get("TENANT_ID")
USER_EMAIL = os.environ.get("USER_EMAIL")

# Validate configuration
if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID, USER_EMAIL]):
    logger.error("Missing required environment variables!")
    raise ValueError("Missing required environment variables!")

logger.info(f"Starting mail relay for {USER_EMAIL}")

# MSAL configuration
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]

# Initialize MSAL application
try:
    msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    logger.info("MSAL application initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize MSAL application: {str(e)}")
    raise

def get_access_token():
    """Get OAuth access token for Graph API"""
    logger.info("Requesting new access token")
    try:
        # First try to get token from cache
        result = msal_app.acquire_token_silent(scopes=SCOPE, account=None)
        
        if not result:
            logger.info("No token in cache, requesting new token")
            result = msal_app.acquire_token_for_client(scopes=SCOPE)
        
        if "access_token" in result:
            logger.info("Successfully acquired access token")
            return result["access_token"]
        else:
            error_msg = f"Failed to get token: {result.get('error_description')}"
            logger.error(error_msg)
            raise Exception(error_msg)
    except Exception as e:
        logger.error(f"Error getting access token: {str(e)}")
        raise

def send_email_via_graph(access_token, to_address, subject, body):
    """Send email using Microsoft Graph API"""
    logger.info(f"Sending email via Graph API to: {to_address}")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    email_data = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "Text",
                "content": body
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": to_address
                    }
                }
            ]
        },
        "saveToSentItems": "true"
    }
    
    try:
        response = requests.post(
            'https://graph.microsoft.com/v1.0/users/' + USER_EMAIL + '/sendMail',
            headers=headers,
            data=json.dumps(email_data)
        )
        response.raise_for_status()
        logger.info("Email sent successfully via Graph API")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending email via Graph API: {str(e)}")
        if hasattr(e.response, 'text'):
            logger.error(f"Graph API Error details: {e.response.text}")
        raise Exception(f"Failed to send email via Graph API: {str(e)}")

@app.route("/healthcheck", methods=["GET"])
def healthcheck():
    """Simple health check endpoint"""
    try:
        # Test token acquisition
        get_access_token()
        return {"status": "healthy", "message": "Service is running and can acquire tokens"}, 200
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500

@app.route("/", methods=["POST"])
def handle_email():
    try:
        # Get email details from request
        data = request.json
        logger.info(f"Received email request to: {data.get('to', 'MISSING')}")
        
        to_address = data.get("to")
        subject = data.get("subject")
        body = data.get("body")
        
        if not all([to_address, subject, body]):
            logger.error("Missing required fields in request")
            return {"error": "Missing required fields"}, 400

        # Get access token
        access_token = get_access_token()
        
        # Send email using Graph API
        send_email_via_graph(access_token, to_address, subject, body)

        return {"status": "success", "message": "Email sent successfully"}

    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=587) 