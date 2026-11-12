import datetime
import http.server
import os
import sqlite3
import socketserver
import ssl
import subprocess

PORT = 8080
HOST = "127.0.0.1"

SOURCES = ["pastebin", "pastesio", "github", "dpaste", "pastecode", "gitlab"]

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
        with sqlite3.connect("logs/tracker.db") as conn:
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

    colors = {
        "pastebin": "#58a6ff",
        "pastesio": "#00ff41",
        "github":  "#bc8cff",
        "dpaste":  "#e06c75",
        "pastecode": "#f0883e",
        "gitlab":  "#fc6d26",
    }
    icons = {"pastebin": "📋", "pastesio": "📄", "github": "💻", "dpaste": "📝", "pastecode": "📌", "gitlab": "🦊"}
    display_names = {"pastebin": "Pastebin", "pastesio": "Pastes.io", "github": "GitHub", "dpaste": "Dpaste", "pastecode": "PasteCode", "gitlab": "GitLab"}
    source_order = {"pastebin": 0, "pastesio": 1, "github": 2, "dpaste": 3, "pastecode": 4, "gitlab": 5}

    labels_row = '<div class="src-row src-header"><span class="src-cell src-cell-icon"></span><span class="src-cell src-cell-name">source</span><span class="src-cell src-cell-num">raw</span><span class="src-cell src-cell-num">pw</span><span class="src-cell src-cell-num">sec</span><span class="src-cell src-cell-bar"></span></div>'

    rows_sorted = sorted(rows, key=lambda r: source_order.get(r[0], 99))
    sources_rows = ""
    for name, raw, pw, sec in rows_sorted:
        color = colors[name]
        label = display_names[name]
        suffix = " <span class=\"attempts\">[" + fm(pio) + " tries]</span>" if name == "pastesio" and pio else ""
        bar_pct = pct(pw)
        sources_rows += (
            "<div class=\"src-row\" style=\"--src-color: " + color + ";\">"
            + "<span class=\"src-cell src-cell-icon\">" + icons[name] + "</span>"
            + "<span class=\"src-cell src-cell-name\">" + label + suffix + "</span>"
            + "<span class=\"src-cell src-cell-num\">" + fm(raw) + "</span>"
            + "<span class=\"src-cell src-cell-num pw\">" + fm(pw) + "</span>"
            + "<span class=\"src-cell src-cell-num sec\">" + fm(sec) + "</span>"
            + "<span class=\"src-cell src-cell-bar\"><span class=\"src-bar\" style=\"width: " + bar_pct + "%;\"></span></span>"
            + "</div>\n"
        )

    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>scavenger :: dashboard</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,400;0,600;0,700;1,400&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:       #0a0a0e;
    --bg-panel:#0f0f14;
    --fg:       #c0c4d0;
    --fg-dim:   #555770;
    --fg-bright:#e0e4f0;
    --green:    #00ff41;
    --blue:     #58a6ff;
    --purple:   #bc8cff;
    --red:      #e06c75;
    --orange:   #f0883e;
    --gitlab-orange: #fc6d26;
    --border:   #1a1a28;
    --glow-green: 0 0 6px rgba(0,255,65,0.15);
  }

  body {
    font-family: "JetBrains Mono", "Fira Code", "Cascadia Code", "Courier New", monospace;
    background: var(--bg);
    color: var(--fg);
    display: flex;
    justify-content: center;
    padding: 2rem 1rem;
    min-height: 100vh;
    line-height: 1.5;
  }

  /* CRT scan-line overlay */
  body::after {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background: repeating-linear-gradient(
      0deg,
      rgba(0,0,0,0.03) 0px,
      rgba(0,0,0,0.03) 1px,
      transparent 1px,
      transparent 3px
    );
    z-index: 999;
  }

  .app { width: min(820px, 100%); }

  /* ===== HEADER ===== */
  .header {
    margin-bottom: 1.5rem;
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    line-height: 1;
  }
  .header .badge {
    display: inline-block;
    border: 1px solid var(--border);
    padding: 0.35rem 0.6rem;
    font-size: 0.65rem;
    font-weight: 700;
    color: var(--green);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  .header .status {
    font-size: 0.6rem;
    color: var(--fg-dim);
    letter-spacing: 0.05em;
    margin-left: auto;
  }
  .header .status .live {
    color: var(--green);
  }
  .header .status .live::before {
    content: "● ";
    animation: pulse 2s ease-in-out infinite;
  }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

  /* ===== OVERVIEW CARDS ===== */
  .stat-cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.6rem;
    margin-bottom: 1.5rem;
  }
  .stat-card {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    padding: 0.85rem 1rem;
    text-align: center;
    transition: border-color 0.2s, box-shadow 0.2s;
  }
  .stat-card:hover {
    border-color: var(--green);
    box-shadow: var(--glow-green);
  }
  .stat-card .num {
    font-size: 1.6rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    line-height: 1.2;
  }
  .stat-card .num.raw-num { color: var(--blue); }
  .stat-card .num.pw-num  { color: var(--green); }
  .stat-card .num.sec-num { color: var(--purple); }
  .stat-card .label {
    font-size: 0.6rem;
    color: var(--fg-dim);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-top: 0.2rem;
  }

  /* ===== SOURCE TABLE ===== */
  .src-table {
    border: 1px solid var(--border);
    background: var(--bg-panel);
    overflow: hidden;
  }
  .src-row {
    display: grid;
    grid-template-columns: 1.6rem 1fr 4.5rem 4.5rem 4.5rem 1fr;
    align-items: center;
    gap: 0;
    padding: 0.55rem 1rem;
    border-bottom: 1px solid var(--border);
    transition: background 0.15s;
    font-size: 0.78rem;
  }
  .src-row:last-child { border-bottom: none; }
  .src-row:hover {
    background: rgba(0,255,65,0.03);
  }
  .src-header {
    color: var(--fg-dim);
    text-transform: uppercase;
    font-size: 0.6rem;
    letter-spacing: 0.12em;
    border-bottom: 1px solid var(--border);
    padding: 0.5rem 1rem;
  }
  .src-header:hover { background: transparent; }

  .src-cell { display: flex; align-items: center; }
  .src-cell-icon  { font-size: 0.9rem; justify-content: center; }
  .src-cell-name  { font-weight: 600; color: var(--fg-bright); padding-left: 0.4rem; }
  .src-cell-num   { justify-content: flex-end; font-variant-numeric: tabular-nums; }
  .src-cell-num.pw  { color: var(--green); }
  .src-cell-num.sec { color: var(--purple); }
  .src-cell-bar   { padding-left: 0.6rem; }

  .attempts {
    color: var(--fg-dim);
    font-weight: 400;
    font-size: 0.65rem;
  }

  .src-bar {
    display: block;
    height: 3px;
    background: var(--src-color, var(--green));
    border-radius: 0;
    transition: width 0.8s ease;
    box-shadow: 0 0 4px var(--src-color, var(--green));
  }

  /* ===== FOOTER ===== */
  .footer {
    margin-top: 1.5rem;
    text-align: center;
    font-size: 0.55rem;
    color: var(--border);
    letter-spacing: 0.05em;
  }
  .footer::before {
    content: "━".repeat(40);
    display: block;
    margin-bottom: 0.5rem;
    opacity: 0.4;
  }

  /* ===== RESPONSIVE ===== */
  @media (max-width: 680px) {
    .stat-cards { gap: 0.4rem; }
    .stat-card .num { font-size: 1.3rem; }
    .src-row {
      grid-template-columns: 1.4rem 1fr 3.2rem 3.2rem 3.2rem 1fr;
      font-size: 0.7rem;
      padding: 0.45rem 0.7rem;
    }
    .src-header { font-size: 0.55rem; padding: 0.4rem 0.7rem; }
    .src-cell-bar { display: none; }
  }
  @media (max-width: 480px) {
    body { padding: 1rem 0.5rem; }
    .stat-cards { grid-template-columns: repeat(3, 1fr); gap: 0.3rem; }
    .stat-card { padding: 0.6rem 0.5rem; }
    .stat-card .num { font-size: 1.1rem; }
    .src-row {
      grid-template-columns: 1.2rem 1fr 2.6rem 2.6rem 2.6rem;
      font-size: 0.62rem;
      padding: 0.4rem 0.5rem;
    }
    .src-cell-bar { display: none; }
    .header { flex-wrap: wrap; gap: 0.4rem; }
    .header .status { margin-left: 0; }
  }
</style>
</head>
<body>
<div class="app">
  <div class="header">
    <span class="badge">scavenger/dashboard</span>
    <span class="status"><span class="live">online</span> · refresh 30s</span>
  </div>

  <div class="stat-cards">
    <div class="stat-card"><div class="num raw-num">""" + fm(totals["raw"]) + """</div><div class="label">Raw Pastes</div></div>
    <div class="stat-card"><div class="num pw-num">""" + fm(totals["passwords"]) + """</div><div class="label">Passwords</div></div>
    <div class="stat-card"><div class="num sec-num">""" + fm(totals["sensitive"]) + """</div><div class="label">Secrets</div></div>
  </div>

  <div class="src-table">
""" + labels_row + sources_rows + """
  </div>

  <div class="footer">localhost:""" + str(PORT) + """</div>
</div>
</body>
</html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def handle(self):
        """Catch SSL handshake errors so a single bad client doesn't crash the server."""
        try:
            super().handle()
        except (ssl.SSLError, ConnectionError, OSError) as e:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            print(ts + " SSL/connection error: " + str(e))

    def do_GET(self):
        self.close_connection = True
        if self.path == "/":
            page = build_page()
            self.send_response(200)
            self.send_header("Connection", "close")
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
    httpd.daemon_threads = True
    httpd.allow_reuse_address = True
    cert = "logs/dashboard.pem"
    if not os.path.exists(cert):
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-keyout", cert,
            "-out", cert, "-days", "3650", "-nodes",
            "-subj", "/CN=localhost",
        ], capture_output=True)
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(cert)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    print("dashboard: https://" + HOST + ":" + str(PORT))
    httpd.serve_forever()