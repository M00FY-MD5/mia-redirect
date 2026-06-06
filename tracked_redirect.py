#!/usr/bin/env python3
"""Tracked redirect service — counts every click then forwards. Deploy to Porter."""
import json, os
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

LOG_DIR = os.path.dirname(os.path.abspath(__file__))
CLICK_LOG = os.path.join(LOG_DIR, "clicks.jsonl")

# Where each slug redirects to
REDIRECTS = {
    "of": "https://onlyfans.com/mia_bluebird?utm_source=miabluebird&utm_medium=tracked",
    "x": "https://x.com/0xMiaBluebird",
    "ig": "https://www.instagram.com/miabluebirdx0?igsh=OXkzNHNwdWVqYWZo&utm_source=qr",
}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.strip("/")
        
        if path in REDIRECTS:
            self.log_click(path)
            self.send_response(302)
            self.send_header("Location", REDIRECTS[path])
            self.end_headers()
            return
        
        if path == "stats":
            stats = self.get_stats()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode())
            return
        
        self.send_response(404)
        self.end_headers()

    def log_click(self, slug):
        event = {
            "slug": slug,
            "ip": self.client_address[0],
            "user_agent": self.headers.get("User-Agent", "")[:200],
            "referer": self.headers.get("Referer", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(CLICK_LOG, "a") as f:
            f.write(json.dumps(event) + "\n")

    def get_stats(self):
        clicks = {"of": 0, "x": 0, "ig": 0}
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_clicks = {"of": 0, "x": 0, "ig": 0}
        
        if os.path.exists(CLICK_LOG):
            with open(CLICK_LOG) as f:
                for line in f:
                    try:
                        e = json.loads(line.strip())
                        slug = e.get("slug", "")
                        clicks[slug] = clicks.get(slug, 0) + 1
                        if e.get("timestamp", "").startswith(today):
                            today_clicks[slug] = today_clicks.get(slug, 0) + 1
                    except:
                        pass
        
        return {
            "total": clicks,
            "today": today_clicks,
            "total_all": sum(clicks.values()),
            "today_all": sum(today_clicks.values()),
        }

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🔗 Tracked redirects on :{port}")
    print(f"   /of → OF | /x → X | /ig → IG | /stats → analytics")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
