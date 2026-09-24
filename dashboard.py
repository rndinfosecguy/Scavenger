import datetime
import http.server
import os
import sqlite3
import socketserver
import ssl
import subprocess

PORT = 8080
HOST = "127.0.0.1"

SOURCES = ["pastebin", "pastesio", "github"]

DATA_DIRS = {
    "raw": "data/raw_pastes",
    "passwords": "data/files_with_passwords",
    "sensitive": "data/otherSensitivePastes",
}


def count_files(path):
    try:
        return len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
    except FileNotFoundError:
        return 0


def count_pastesio_attempts():
    try:
        conn = sqlite3.connect("logs/tracker.db")
        return conn.execute("SELECT COUNT(*) FROM tried_pastesio").fetchone()[0]
    except Exception:
        return 0


def collect_stats():
    rows = []
    totals = {"raw": 0, "passwords": 0, "sensitive": 0}

    for source in SOURCES:
        raw = count_files(DATA_DIRS["raw"] + "/" + source)
        pw = count_files(DATA_DIRS["passwords"] + "/" + source)
        sec = count_files(DATA_DIRS["sensitive"] + "/" + source)
        rows.append((source, raw, pw, sec))
        totals["raw"] += raw
        totals["passwords"] += pw
        totals["sensitive"] += sec

    pio_attempts = count_pastesio_attempts()
    return rows, totals, pio_attempts


def build_page():
    rows, totals, pio = collect_stats()
    total_pastes = totals["raw"] or 1

    def fm(v):
        return f"{v:,}"

    def pct(v):
        return f"{v / total_pastes * 100:.1f}"

    cards = ""
    sources_html = ""
    colors = {
        "pastebin": ("#58a6ff", "#1c2e4a"),
        "pastesio": ("#3fb950", "#1a3a24"),
        "github": ("#bc8cff", "#2a1f40"),
    }
    icons = {"pastebin": "📋", "pastesio": "📄", "github": "💻"}
    display_names = {"pastebin": "Pastebin", "pastesio": "Pastes.io", "github": "GitHub"}

    for name, raw, pw, sec in rows:
        color, bg = colors[name]
        label = display_names[name] + (" (" + fm(pio) + " attempts)" if name == "pastesio" and pio else "")
        bar_pct = pct(pw)
        sources_html += (
            "<div class=\"src-card\" style=\"border-left-color: " + color + ";\">"
            + "<div class=\"src-head\">"
            + "<span class=\"src-icon\">" + icons[name] + "</span>"
            + "<span class=\"src-name\">" + label + "</span>"
            + "</div>"
            + "<div class=\"src-stats\">"
            + "<div class=\"stat\"><span class=\"stat-label\">Raw</span><span class=\"stat-value\">" + fm(raw) + "</span></div>"
            + "<div class=\"stat\"><span class=\"stat-label\">Passwords</span><span class=\"stat-value pw\">" + fm(pw) + "</span></div>"
            + "<div class=\"stat\"><span class=\"stat-label\">Secrets</span><span class=\"stat-value sec\">" + fm(sec) + "</span></div>"
            + "</div>"
            + "<div class=\"bar-wrap\"><div class=\"bar\" style=\"width: " + bar_pct + "%; background: " + color + ";\"></div></div>"
            + "</div>\n"
        )

    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>Scavenger Dashboard</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: #0a0c10; color: #e1e4e8;
    display: flex; justify-content: center; padding: 3rem 1.5rem;
    min-height: 100vh;
  }
  .app { width: min(720px, 100%); }

  .header { margin-bottom: 2rem; }
  .header h1 { font-size: 1.5rem; font-weight: 700; letter-spacing: -0.02em; }
  .header .sub { color: #6e7387; font-size: 0.88rem; margin-top: 0.2rem; }

  .stat-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; margin-bottom: 1.75rem; }
  .stat-card {
    background: linear-gradient(135deg, #171922 0%, #1c1e28 100%);
    border: 1px solid #282a35; border-radius: 12px; padding: 1.1rem 1.2rem;
    transition: transform 0.15s, box-shadow 0.15s;
  }
  .stat-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.4); }
  .stat-card .num { font-size: 1.8rem; font-weight: 700; letter-spacing: -0.02em; }
  .stat-card .label { font-size: 0.82rem; color: #6e7387; margin-top: 0.25rem; text-transform: uppercase; letter-spacing: 0.05em; }
  .stat-card .num.raw-num { color: #58a6ff; }
  .stat-card .num.pw-num { color: #3fb950; }
  .stat-card .num.sec-num { color: #bc8cff; }

  .src-card {
    background: #151720; border: 1px solid #282a35; border-left: 4px solid;
    border-radius: 12px; padding: 1.2rem 1.4rem; margin-bottom: 0.75rem;
    transition: transform 0.15s, box-shadow 0.15s;
  }
  .src-card:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(0,0,0,0.35); }
  .src-head { display: flex; align-items: center; gap: 0.55rem; margin-bottom: 0.75rem; }
  .src-icon { font-size: 1.1rem; }
  .src-name { font-weight: 600; font-size: 1rem; }
  .src-stats { display: flex; gap: 1.5rem; flex-wrap: wrap; }
  .stat { display: flex; flex-direction: column; gap: 0.15rem; }
  .stat-label { font-size: 0.75rem; color: #6e7387; text-transform: uppercase; letter-spacing: 0.06em; }
  .stat-value { font-size: 1.1rem; font-weight: 600; font-variant-numeric: tabular-nums; }
  .stat-value.pw { color: #3fb950; }
  .stat-value.sec { color: #bc8cff; }

  .bar-wrap { margin-top: 0.7rem; height: 4px; background: #282a35; border-radius: 4px; overflow: hidden; }
  .bar { height: 100%; border-radius: 4px; transition: width 0.5s; }

  .footer { margin-top: 1.5rem; text-align: center; font-size: 0.8rem; color: #3d4053; }
  .footer .dot { color: #282a35; }

  @media (max-width: 540px) {
    body { padding: 1.5rem 1rem; }
    .stat-cards { gap: 0.5rem; }
    .stat-card { padding: 0.9rem 1rem; }
    .stat-card .num { font-size: 1.4rem; }
    .src-stats { gap: 1rem; }
  }
</style>
</head>
<body>
<div class="app">
  <div class="header">
    <h1>Scavenger Dashboard</h1>
    <p class="sub">Auto-refreshes every 30s</p>
  </div>
  <div class="stat-cards">
    <div class="stat-card"><div class="num raw-num">""" + fm(totals["raw"]) + """</div><div class="label">Raw Pastes</div></div>
    <div class="stat-card"><div class="num pw-num">""" + fm(totals["passwords"]) + """</div><div class="label">Passwords</div></div>
    <div class="stat-card"><div class="num sec-num">""" + fm(totals["sensitive"]) + """</div><div class="label">Secrets</div></div>
  </div>
""" + sources_html + """
  <div class="footer"><span class="dot">·</span> localhost:""" + str(PORT) + """ <span class="dot">·</span></div>
</div>
</body>
</html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            page = build_page()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        print(ts + " " + fmt % args)


with socketserver.ThreadingTCPServer((HOST, PORT), Handler) as httpd:
    cert = "logs/dashboard.pem"
    if not os.path.exists(cert):
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-keyout", cert,
            "-out", cert, "-days", "3650", "-nodes",
            "-subj", "/CN=localhost",
        ], capture_output=True)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    print("dashboard: https://" + HOST + ":" + str(PORT))
    httpd.serve_forever()