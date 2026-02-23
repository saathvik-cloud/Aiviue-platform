"""
One-time script to obtain a Google OAuth refresh token.

Usage:
  1. Go to Google Cloud Console > APIs & Services > Credentials
  2. Edit your OAuth 2.0 Client ID
  3. Add http://localhost:8080 to Authorized redirect URIs and save
  4. Run this script:  python scripts/get_google_refresh_token.py
  5. A browser window opens — sign in with your platform Google account
  6. After consent, the refresh token is printed
  7. Paste it into .env as GOOGLE_OAUTH_REFRESH_TOKEN
"""

import json
import sys
import http.server
import urllib.parse
import webbrowser
import threading

CLIENT_ID = input("Paste your OAuth Client ID (or press Enter to use from .env): ").strip()
CLIENT_SECRET = input("Paste your OAuth Client Secret (or press Enter to use from .env): ").strip()

if not CLIENT_ID or not CLIENT_SECRET:
    try:
        from dotenv import dotenv_values
        env = dotenv_values(".env")
        CLIENT_ID = CLIENT_ID or env.get("GOOGLE_OAUTH_CLIENT_ID", "").strip('"')
        CLIENT_SECRET = CLIENT_SECRET or env.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip('"')
    except ImportError:
        print("python-dotenv not installed. Please provide client ID and secret manually.")
        sys.exit(1)

if not CLIENT_ID or not CLIENT_SECRET:
    print("Client ID and Secret are required.")
    sys.exit(1)

REDIRECT_URI = "http://localhost:8080"
SCOPES = "https://www.googleapis.com/auth/calendar"
AUTH_CODE = None


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global AUTH_CODE
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        AUTH_CODE = params.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h2>Authorization successful! You can close this tab.</h2>")

    def log_message(self, format, *args):
        pass


auth_url = (
    "https://accounts.google.com/o/oauth2/v2/auth?"
    f"client_id={CLIENT_ID}&"
    f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
    "response_type=code&"
    f"scope={urllib.parse.quote(SCOPES)}&"
    "access_type=offline&"
    "prompt=consent"
)

print(f"\nOpening browser for Google consent...\n{auth_url}\n")
webbrowser.open(auth_url)

server = http.server.HTTPServer(("localhost", 8080), CallbackHandler)
print("Waiting for callback on http://localhost:8080 ...")
server.handle_request()

if not AUTH_CODE:
    print("No authorization code received.")
    sys.exit(1)

print(f"\nAuthorization code received. Exchanging for refresh token...")

import urllib.request

token_data = urllib.parse.urlencode({
    "code": AUTH_CODE,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code",
}).encode()

req = urllib.request.Request(
    "https://oauth2.googleapis.com/token",
    data=token_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)

try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())
except urllib.error.HTTPError as e:
    print(f"Token exchange failed: {e.read().decode()}")
    sys.exit(1)

refresh_token = result.get("refresh_token")
if refresh_token:
    print(f"\n{'='*60}")
    print(f"REFRESH TOKEN (paste into .env as GOOGLE_OAUTH_REFRESH_TOKEN):")
    print(f"\n{refresh_token}\n")
    print(f"{'='*60}")
else:
    print(f"\nNo refresh_token in response. Full response:\n{json.dumps(result, indent=2)}")
    print("\nMake sure you used prompt=consent and access_type=offline.")
