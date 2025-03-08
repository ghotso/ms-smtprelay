import os
from flask import Flask, request
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import msal

app = Flask(__name__)

# Configuration
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
TENANT_ID = os.environ.get("TENANT_ID", "common")
USER_EMAIL = os.environ.get("USER_EMAIL")

# MSAL configuration
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://outlook.office365.com/.default"]

# Initialize MSAL application
msal_app = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET
)

def get_access_token():
    """Get OAuth access token for SMTP authentication"""
    result = msal_app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Failed to get token: {result.get('error_description')}")

class OAuth2Authenticator:
    def __init__(self):
        self.access_token = None

    def authenticate(self, mechanism, authobject):
        if mechanism == "XOAUTH2":
            auth_string = f"user={USER_EMAIL}\x01auth=Bearer {self.access_token}\x01\x01"
            return auth_string.encode()
        return None

@app.route("/", methods=["POST"])
def handle_email():
    try:
        # Get email details from request
        data = request.json
        to_address = data.get("to")
        subject = data.get("subject")
        body = data.get("body")
        
        if not all([to_address, subject, body]):
            return {"error": "Missing required fields"}, 400

        # Create message
        msg = MIMEMultipart()
        msg["From"] = USER_EMAIL
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Set up SMTP connection
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            
            # Get fresh token and set up authenticator
            authenticator = OAuth2Authenticator()
            authenticator.access_token = get_access_token()
            
            # Enable SMTP auth with custom authenticator
            server.ehlo()
            server.auth_handler.append("XOAUTH2", authenticator.authenticate)
            server.auth("XOAUTH2", None)
            
            # Send email
            server.send_message(msg)

        return {"status": "success", "message": "Email sent successfully"}

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=587) 