#!/usr/bin/env python3
"""
Simple Flask server to handle OAuth redirects for testing.
This server captures the authorization code from the redirect URL.
"""

from flask import Flask, request, redirect, url_for, jsonify
import webbrowser
from urllib.parse import urlencode
import threading
import time

app = Flask(__name__)

# Store the authorization code globally
auth_code = None
server_running = False

@app.route('/auth/facebook/callback')
def facebook_callback():
    """Handle Facebook OAuth callback"""
    global auth_code
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        return f"Error: {error} - {request.args.get('error_description', '')}"

    if code:
        auth_code = code
        return """
        <h1>✅ Facebook Authorization Successful!</h1>
        <p>You can close this window and return to the terminal.</p>
        <p>Authorization code has been captured.</p>
        <script>
            window.close();
        </script>
        """
    else:
        return "No authorization code received", 400

@app.route('/auth/instagram/callback')
def instagram_callback():
    """Handle Instagram OAuth callback"""
    global auth_code
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        return f"Error: {error} - {request.args.get('error_description', '')}"

    if code:
        auth_code = code
        return """
        <h1>✅ Instagram Authorization Successful!</h1>
        <p>You can close this window and return to the terminal.</p>
        <p>Authorization code has been captured.</p>
        <script>
            window.close();
        </script>
        """
    else:
        return "No authorization code received", 400

def get_auth_code():
    """Return the captured authorization code"""
    global auth_code
    return auth_code

def reset_auth_code():
    """Reset the authorization code"""
    global auth_code
    auth_code = None

def run_server():
    """Run the Flask server in a separate thread"""
    global server_running
    server_running = True
    app.run(port=5000, debug=False)
    server_running = False

def start_oauth_server():
    """Start the OAuth server and return the thread"""
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait a moment for server to start
    time.sleep(2)

    return server_thread

if __name__ == "__main__":
    print("🚀 Starting OAuth Redirect Server")
    print("Server will run on http://localhost:5000")
    print("This server handles Facebook and Instagram OAuth callbacks")
    print("Press Ctrl+C to stop the server")

    # Start the server
    start_oauth_server()

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")