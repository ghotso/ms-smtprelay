import os
import logging
from flask import Flask, request
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import msal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('smtp_relay')

app = Flask(__name__)

# Configuration
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
TENANT_ID = os.environ.get("TENANT_ID")
USER_EMAIL = os.environ.get("USER_EMAIL")

# Validate configuration
if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID, USER_EMAIL]):
    logger.error("Missing required environment variables!")
    raise ValueError("Missing required environment variables!")

logger.info(f"Starting SMTP relay for {USER_EMAIL} using {SMTP_SERVER}:{SMTP_PORT}")

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
    """Get OAuth access token for SMTP authentication"""
    logger.info("Requesting new access token")
    try:
        result = msal_app.acquire_token_for_client(scopes=SCOPE)
        if "access_token" in result:
            logger.info("Successfully acquired new access token")
            return result["access_token"]
        else:
            error_msg = f"Failed to get token: {result.get('error_description')}"
            logger.error(error_msg)
            raise Exception(error_msg)
    except Exception as e:
        logger.error(f"Error getting access token: {str(e)}")
        raise

class OAuth2Authenticator:
    def __init__(self):
        self.access_token = None

    def authenticate(self, mechanism, authobject):
        if mechanism == "XOAUTH2":
            logger.debug("Performing XOAUTH2 authentication")
            auth_string = f"user={USER_EMAIL}\x01auth=Bearer {self.access_token}\x01\x01"
            return auth_string.encode()
        return None

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

        # Create message
        msg = MIMEMultipart()
        msg["From"] = USER_EMAIL
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Set up SMTP connection
        logger.info(f"Establishing SMTP connection to {SMTP_SERVER}:{SMTP_PORT}")
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            logger.debug("TLS connection established")
            
            # Get fresh token and set up authenticator
            authenticator = OAuth2Authenticator()
            authenticator.access_token = get_access_token()
            
            # Enable SMTP auth with custom authenticator
            server.ehlo()
            server.auth_handler.append("XOAUTH2", authenticator.authenticate)
            server.auth("XOAUTH2", None)
            logger.info("Successfully authenticated with SMTP server")
            
            # Send email
            server.send_message(msg)
            logger.info(f"Email sent successfully to {to_address}")

        return {"status": "success", "message": "Email sent successfully"}

    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}, 500

if __name__ == "__main__":
    # Note: This should only be used for development
    app.run(host="0.0.0.0", port=587) 