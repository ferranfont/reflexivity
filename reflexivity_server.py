import http.server
import socketserver
import os
import subprocess
import time
import urllib.parse
import threading
import sys
from pathlib import Path

# Config
PORT = 8000
BASE_DIR = Path(__file__).parent.absolute()
HTML_DIR = BASE_DIR / "html"
SCRIPT_PATH = BASE_DIR / "show_company_profile.py"
INACTIVITY_TIMEOUT = 1800  # 30 minutes in seconds

# Global state for inactivity
last_activity = time.time()

def monitor_inactivity():
    """Check for inactivity and shut down if timeout reached."""
    global last_activity
    print(f"[SERVER] Auto-shutdown monitor started (Timeout: {INACTIVITY_TIMEOUT/60:.0f} mins)")
    while True:
        time.sleep(60)  # Check every minute
        elapsed = time.time() - last_activity
        if elapsed > INACTIVITY_TIMEOUT:
            print(f"[SERVER] No activity for {elapsed/60:.1f} mins. Shutting down...")
            os._exit(0) # Force exit



class ReflexivityHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Update activity timer
        global last_activity
        last_activity = time.time()

        # Parse URL
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # 1. Handle Profile Request: /profile/NVDA

        if path.startswith("/profile/"):
            symbol = path.split("/")[-1].upper()
            self.handle_profile_request(symbol)
            return

        # 2. Handle Theme Request: /theme/Accelerated_Computing
        if path.startswith("/theme/"):
            # Extract theme name (underscores back to spaces)
            theme_url_name = path.split("/theme/")[-1]
            # Decode URL encoding first (e.g. %20 for spaces)
            theme_url_name = urllib.parse.unquote(theme_url_name)
            # We treat the URL part as the "key". Since show_main links map to _detail.html directly,
            # we need to intercept those OR change show_main links to /theme/.
            # For now, let's assume we change show_main to link to /theme/{processed_name}
            # so we can parse it back to "Accelerated Computing"
            
            # Reconstruct real theme name: "Accelerated_Computing" -> "Accelerated Computing"
            # But wait, show_main uses .replace(' ','_').replace('-','_').
            # This is lossy. Ideally show_main passes the raw name or a recoverable id.
            # Best approach: Use the filename logic from show_theme to match.
            # Actually, simpler: Pass the raw name in URL? /theme/Accelerated%20Computing
            
            self.handle_theme_request(theme_url_name)
            return

        # 3. Serve Static Files (Default to HTML_DIR)
        # If path is root, serve main_trends.html (UPDATED DEFAULT)
        if path == "/" or path == "/main_trends.html":
             self.path = "/main_trends.html"
        
        # ... existing static logic ...
        # (Be careful not to overwrite the static logic heavily if not needed)
        
        # Map requests to HTML_DIR
        file_path = HTML_DIR / path.lstrip("/")
        
        if file_path.exists() and file_path.is_file():
            # serve file from html dir
            self.send_response(200)
            if str(file_path).endswith(".css"):
                self.send_header("Content-type", "text/css")
            elif str(file_path).endswith(".js"):
                self.send_header("Content-type", "application/javascript")
            else:
                self.send_header("Content-type", "text/html")
            self.end_headers()
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            # If 404, maybe it's a theme detail page we can infer?
            # E.g. /accelerated_computing_detail.html
            # It's hard to infer "Accelerated Computing" from "accelerated_computing".
            # Better to use explicit /theme/ route.
            self.send_error(404, f"File not found: {self.path}")

    def handle_theme_request(self, theme_input):
        # theme_input should be something we can pass to show_theme.py
        # If getting from /theme/Accelerated_Computing (underscores), convert to spaces?
        # Or just pass as is if show_theme handles it?
        # show_theme.py takes args and does `theme.lower().replace(' ', '_')` for filenames.
        # So passing "Accelerated Computing" works best.
        
        # Strategy: Try to be smart. Replace underscores with spaces for the script argument.
        theme_name = theme_input.replace("_", " ") # restore spaces
        
        # Expected filename by show_theme.py
        # It uses lower().replace(' ', '_') 
        safe_name = theme_name.lower().replace(" ", "_").replace("-", "_")
        html_filename = f"{safe_name}_detail.html"
        html_path = HTML_DIR / html_filename
        
        generate = False
        if not html_path.exists():
            print(f"[SERVER] Theme {html_filename} missing. Generating for '{theme_name}'...")
            generate = True
        else:
            age = time.time() - os.path.getmtime(html_path)
            if age > 86400: # 24h
                 print(f"[SERVER] Theme {html_filename} old. Regenerating...")
                 generate = True
                 
        if generate:
            try:
                print(f"[SERVER] Running show_theme.py \"{theme_name}\"")
                # Using sys.executable to ensure same python env
                subprocess.run([sys.executable, str(BASE_DIR / "show_theme.py"), theme_name], check=True, cwd=str(BASE_DIR))
            except Exception as e:
                self.send_error(500, f"Error generating theme: {e}")
                return

        # Redirect to the resulting HTML file
        self.send_response(302)
        self.send_header('Location', f"/{html_filename}")
        self.end_headers()

    def handle_profile_request(self, symbol):
        # ... existing profile logic ...
        profile_filename = f"{symbol}_profile.html"
        profile_path = HTML_DIR / profile_filename
        
        generate = False
        
        # Check existence
        if not profile_path.exists():
            print(f"[SERVER] {profile_filename} not found. Generating...")
            generate = True
        else:
            # Check age (24 hours = 86400 seconds)
            age = time.time() - os.path.getmtime(profile_path)
            if age > 86400:
                print(f"[SERVER] {profile_filename} is old ({age:.0f}s). Regenerating...")
                generate = True
            else:
                print(f"[SERVER] {profile_filename} is fresh.")

        if generate:
            try:
                # Run the generation script
                print(f"[SERVER] Executing: python show_company_profile.py {symbol}")
                subprocess.run(["python", str(SCRIPT_PATH), symbol], check=True, cwd=str(BASE_DIR))
            except Exception as e:
                self.send_error(500, f"Error generating profile: {e}")
                return

        # Redirect to the generated HTML file
        self.send_response(302)
        self.send_header('Location', f"/{profile_filename}")
        self.end_headers()

if __name__ == "__main__":
    print(f"Starting Reflexivity Server at http://localhost:{PORT}")
    print(f"Server Root: {BASE_DIR}")
    print(f"HTML Dir: {HTML_DIR}")
    print("-------------------------------------------------------")
    
    # Start inactivity monitor
    threading.Thread(target=monitor_inactivity, daemon=True).start()
    
    with socketserver.TCPServer(("", PORT), ReflexivityHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
