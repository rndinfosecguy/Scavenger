import datetime
import http.server
import os
import signal
import socket
import sqlite3
import socketserver
import ssl
import subprocess
import time

PORT = 8080
HOST = "127.0.0.1"

SOURCES = ["pastebin", "pastesio", "github", "dpaste", "pastecode", "gitlab", "ideone", "pastegg"]

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


def count_archived(source, per_archive=48000):
    """Estimate archived paste count: number of <source>_*.zip × per_archive."""
    count = 0
    try:
        for f in os.listdir("archive"):
            if f.startswith(source + "_") and f.endswith(".zip"):
                count += 1
    except FileNotFoundError:
        pass
    return count * per_archive


def get_last_crawled(source):
    """Read the last-crawled timestamp file and return (timestamp, short_display)."""
    try:
        with open("logs/" + source + "_last_crawled.txt") as f:
            ts = float(f.read().strip())
        elapsed = time.time() - ts
        if elapsed < 60:
            return (ts, "just now")
        elif elapsed < 3600:
            return (ts, str(int(elapsed // 60)) + "m ago")
        else:
            hours = int(elapsed // 3600)
            mins = int((elapsed % 3600) // 60)
            return (ts, str(hours) + "h " + str(mins) + "m ago")
    except (FileNotFoundError, ValueError):
        return (0, "never")


def source_is_online(source):
    """Return True if scraper wrote a last-crawled timestamp within the last hour."""
    ts, _ = get_last_crawled(source)
    if ts == 0:
        return False
    return (time.time() - ts) < 3600


def collect_top_types(limit=10):
    """Walk sensitive/password dirs and count detection labels. Returns sorted list of (label, count)."""
    from collections import Counter
    counts = Counter()

    for source in SOURCES:
        # Password dir — all files are email:password
        try:
            for f in os.listdir("data/files_with_passwords/" + source):
                if os.path.isfile(os.path.join("data/files_with_passwords/" + source, f)):
                    counts["email:password"] += 1
        except FileNotFoundError:
            pass

        # Sensitive dir — filenames are {label}_{paste_id}
        try:
            for f in os.listdir("data/otherSensitivePastes/" + source):
                if not os.path.isfile(os.path.join("data/otherSensitivePastes/" + source, f)):
                    continue
                # Label is everything before the last underscore
                label = f.rsplit("_", 1)[0] if "_" in f else f
                if label:
                    counts[label] += 1
        except FileNotFoundError:
            pass

    return counts.most_common(limit)


def collect_recent(limit=10):
    """Return the most recent detection entries sorted by file mtime."""
    entries = []
    for source in SOURCES:
        # Password files (email:password)
        try:
            for f in os.listdir("data/files_with_passwords/" + source):
                path = os.path.join("data/files_with_passwords/" + source, f)
                if not os.path.isfile(path):
                    continue
                entries.append((os.path.getmtime(path), source, "email:password", f))
        except FileNotFoundError:
            pass
        # Sensitive files (label_pasteId)
        try:
            for f in os.listdir("data/otherSensitivePastes/" + source):
                path = os.path.join("data/otherSensitivePastes/" + source, f)
                if not os.path.isfile(path):
                    continue
                label = f.rsplit("_", 1)[0] if "_" in f else f
                entries.append((os.path.getmtime(path), source, label, f))
        except FileNotFoundError:
            pass
    entries.sort(key=lambda x: x[0], reverse=True)
    return entries[:limit]


def collect_stats():
    rows = []
    totals = {"raw": 0, "passwords": 0, "sensitive": 0}

    for source in SOURCES:
        raw = count_files(DATA_DIRS["raw"] + "/" + source) + count_archived(source)
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

    def fm(v):
        return f"{v:,}"

    top_types = collect_top_types(10)
    top_total = max((c for _, c in top_types), default=1)
    top_html = ""
    if top_types:
        top_html = '<div class="top-section"><div class="top-header">top detected</div>'
        for label, count in top_types:
            bar_pct = count / top_total * 100
            top_html += (
                '<div class="top-row">'
                + '<span class="top-label">' + label + '</span>'
                + '<span class="top-bar"><span class="top-fill" style="width: ' + str(bar_pct) + '%;"></span></span>'
                + '<span class="top-count">' + fm(count) + '</span>'
                + '</div>\n'
            )
        top_html += '</div>'

    icons = {"pastebin": "📋", "pastesio": "📄", "github": "💻", "dpaste": "📝", "pastecode": "📌", "gitlab": "🦊", "ideone": "🧩", "pastegg": "🥚"}
    display_names = {"pastebin": "Pastebin", "pastesio": "Pastes.io", "github": "GitHub", "dpaste": "Dpaste", "pastecode": "PasteCode", "gitlab": "GitLab", "ideone": "Ideone", "pastegg": "paste.gg"}

    recent = collect_recent(10)
    recent_html = ""
    if recent:
        recent_html = '<div class="top-section" id="recent-section"><div class="top-header">recent detections</div>'
        for mtime, source, label, _ in recent:
            age = time.time() - mtime
            if age < 60:
                ts = "just now"
            elif age < 3600:
                ts = str(int(age // 60)) + "m ago"
            elif age < 86400:
                ts = str(int(age // 3600)) + "h ago"
            else:
                ts = str(int(age // 86400)) + "d ago"
            recent_html += (
                '<div class="recent-row">'
                + '<span class="recent-time">' + ts + '</span>'
                + '<span class="recent-source">' + icons.get(source, "") + " " + display_names.get(source, source) + '</span>'
                + '<span class="recent-label">' + label + '</span>'
                + '</div>\n'
            )
        recent_html += '</div>'

    icons = {"pastebin": "📋", "pastesio": "📄", "github": "💻", "dpaste": "📝", "pastecode": "📌", "gitlab": "🦊", "ideone": "🧩", "pastegg": "🥚"}
    display_names = {"pastebin": "Pastebin", "pastesio": "Pastes.io", "github": "GitHub", "dpaste": "Dpaste", "pastecode": "PasteCode", "gitlab": "GitLab", "ideone": "Ideone", "pastegg": "paste.gg"}
    source_order = {"pastebin": 0, "pastesio": 1, "github": 2, "dpaste": 3, "pastecode": 4, "gitlab": 5, "ideone": 6, "pastegg": 7}

    labels_row = '<div class="src-row src-header"><span class="src-cell src-cell-icon"></span><span class="src-cell src-cell-name">source</span><span class="src-cell src-cell-num">raw</span><span class="src-cell src-cell-num">pw</span><span class="src-cell src-cell-num">sec</span><span class="src-cell src-cell-tail">scraper status</span></div>'

    rows_sorted = sorted(rows, key=lambda r: source_order.get(r[0], 99))
    sources_rows = ""
    for name, raw, pw, sec in rows_sorted:
        label = display_names[name]
        online = source_is_online(name)
        row_class = " src-row-offline" if not online else ""
        status_dot = "<span class=\"dot-online\">● online</span>" if online else "<span class=\"dot-offline\">● offline</span>"
        _, last_str = get_last_crawled(name)
        tries = " <span class=\"attempts\">[" + fm(pio) + " tries]</span>" if name == "pastesio" and pio else ""
        sources_rows += (
            "<div class=\"src-row" + row_class + "\">"
            + "<span class=\"src-cell src-cell-icon\">" + icons[name] + "</span>"
            + "<span class=\"src-cell src-cell-name\">" + label + tries + "</span>"
            + "<span class=\"src-cell src-cell-num\">" + fm(raw) + "</span>"
            + "<span class=\"src-cell src-cell-num pw\">" + fm(pw) + "</span>"
            + "<span class=\"src-cell src-cell-num sec\">" + fm(sec) + "</span>"
            + "<span class=\"src-cell src-cell-tail\">"
            + status_dot
            + "<span class=\"crawled-at\">" + last_str + "</span>"
            + "</span>"
            + "</div>\n"
        )

    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
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
    align-items: center;
    gap: 0.5rem;
    line-height: 1;
  }
  .header .logo {
    width: 13rem;
    height: 4rem;
    background: url("scavenger_logo.png") no-repeat center;
    background-size: contain;
    border: 0;
  }
  .header .status {
    font-size: 0.6rem;
    color: var(--fg-dim);
    letter-spacing: 0.05em;
    margin-left: auto;
  }

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
    grid-template-columns: 1.6rem 1fr 4.5rem 4.5rem 4.5rem 2fr;
    align-items: center;
    column-gap: 0.5rem;
    padding: 0.55rem 1rem;
    border-bottom: 1px solid var(--border);
    transition: background 0.15s;
    font-size: 0.78rem;
  }
  .src-row:last-child { border-bottom: none; }
  .src-row:hover {
    background: rgba(0,255,65,0.03);
  }
  .src-row-offline .src-cell-icon,
  .src-row-offline .src-cell-name,
  .src-row-offline .src-cell-num {
    opacity: 0.35;
  }
  .src-row-offline:hover {
    background: transparent;
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
  .src-cell-tail  { justify-content: center; gap: 0.25rem; }

  .attempts {
    color: var(--fg-dim);
    font-weight: 400;
    font-size: 0.65rem;
  }

  .dot-online {
    color: var(--green);
    animation: pulse 2s ease-in-out infinite;
  }
  .dot-offline {
    color: var(--red);
  }
  .crawled-at {
    min-width: 6rem;
    text-align: right;
    font-size: 0.6rem;
    font-weight: 400;
    color: var(--fg-dim);
  }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

  /* ===== TOP DETECTED ===== */
  .top-section {
    border: 1px solid var(--border);
    background: var(--bg-panel);
    margin-top: 1rem;
    padding: 0.75rem 1rem;
  }
  .top-header {
    color: var(--fg-dim);
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.5rem;
    padding-bottom: 0.3rem;
    border-bottom: 1px solid var(--border);
  }
  .top-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0;
    font-size: 0.7rem;
  }
  .top-label {
    min-width: 10rem;
    color: var(--fg);
    font-weight: 400;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .top-bar {
    flex: 1;
    height: 5px;
    background: rgba(255,255,255,0.04);
  }
  .top-fill {
    display: block;
    height: 100%;
    background: var(--green);
    transition: width 0.8s ease;
  }
  .top-count {
    min-width: 3.5rem;
    text-align: right;
    font-variant-numeric: tabular-nums;
    color: var(--fg-dim);
  }

  /* ===== RECENT DETECTIONS ===== */
  .recent-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.2rem 0;
    font-size: 0.7rem;
  }
  .recent-time {
    min-width: 4rem;
    color: var(--fg-dim);
    font-size: 0.6rem;
  }
  .recent-source {
    min-width: 7rem;
    color: var(--fg);
    white-space: nowrap;
  }
  .recent-label {
    color: var(--fg-bright);
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
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
      grid-template-columns: 1.4rem 1fr 3.2rem 3.2rem 3.2rem 2fr;
      column-gap: 0.3rem;
      font-size: 0.7rem;
      padding: 0.45rem 0.7rem;
    }
    .src-header { font-size: 0.55rem; padding: 0.4rem 0.7rem; }
  }
  @media (max-width: 480px) {
    .attempts { display: none; }
    body { padding: 1rem 0.5rem; }
    .stat-cards { grid-template-columns: repeat(3, 1fr); gap: 0.3rem; }
    .stat-card { padding: 0.6rem 0.5rem; }
    .stat-card .num { font-size: 1.1rem; }
    .src-row {
      grid-template-columns: 1.2rem 1fr 2.6rem 2.6rem 2.6rem 1fr;
      column-gap: 0.25rem;
      font-size: 0.62rem;
      padding: 0.4rem 0.5rem;
    }
    .header { flex-wrap: wrap; gap: 0.4rem; }
    .header .status { margin-left: 0; }
  }
</style>
</head>
<body>
<div class="app">
  <div class="header">
    <div class="logo"></div>
    <span class="status">updated every 60s</span>
  </div>

  <div class="stat-cards">
    <div class="stat-card"><div class="num raw-num" id="total-raw">""" + fm(totals["raw"]) + """</div><div class="label">Raw Pastes</div></div>
    <div class="stat-card"><div class="num pw-num" id="total-pw">""" + fm(totals["passwords"]) + """</div><div class="label">Passwords</div></div>
    <div class="stat-card"><div class="num sec-num" id="total-sec">""" + fm(totals["sensitive"]) + """</div><div class="label">Secrets</div></div>
  </div>

  <div class="src-table">
""" + labels_row + sources_rows + """
  </div>

""" + top_html + recent_html + """
  <div class="footer">localhost:""" + str(PORT) + """</div>
</div>
<script>
var I={'pastebin':'📋','pastesio':'📄','github':'💻','dpaste':'📝','pastecode':'📌','gitlab':'🦊','ideone':'🧩','pastegg':'🥚'};
var D={'pastebin':'Pastebin','pastesio':'Pastes.io','github':'GitHub','dpaste':'Dpaste','pastecode':'PasteCode','gitlab':'GitLab','ideone':'Ideone','pastegg':'paste.gg'};
(function f(){fetch('/api/stats').then(function(r){return r.json()}).then(function(d){
var c=function(x){return x.toLocaleString('en')};
document.getElementById('total-raw').textContent=c(d.totals.raw);
document.getElementById('total-pw').textContent=c(d.totals.pw);
document.getElementById('total-sec').textContent=c(d.totals.sec);
var rs=document.getElementById('recent-section');
if(rs&&d.recent&&d.recent.length){
var h='<div class="top-header">recent detections</div>';
for(var i=0;i<d.recent.length;i++){
var r=d.recent[i],a=Date.now()/1e3-r.ts;
var t=a<60?'just now':a<3600?Math.floor(a/60)+'m ago':a<86400?Math.floor(a/3600)+'h ago':Math.floor(a/86400)+'d ago';
h+='<div class="recent-row"><span class="recent-time">'+t+'</span><span class="recent-source">'+(I[r.source]||'')+' '+(D[r.source]||r.source)+'</span><span class="recent-label">'+r.label+'</span></div>';
}
rs.innerHTML=h;
}
}).catch(function(e){});
setTimeout(f,60000)})();
</script>
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
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(page.encode("utf-8"))))
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))
        elif self.path == "/api/stats":
            self._serve_stats()
        elif self.path.startswith("/scavenger_logo."):
            # Serve the logo from a fixed path — no user input involved
            logo = "scavenger_logo.png"
            if os.path.exists(logo):
                with open(logo, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Connection", "close")
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        print(ts + " " + fmt % args)

    def _serve_stats(self):
        """Serve /api/stats as JSON for the live-update script."""
        import json
        rows, totals, pio = collect_stats()
        sources = []
        icon_map = {"pastebin": "📋", "pastesio": "📄", "github": "💻", "dpaste": "📝", "pastecode": "📌", "gitlab": "🦊", "ideone": "🧩", "pastegg": "🥚"}
        display_map = {"pastebin": "Pastebin", "pastesio": "Pastes.io", "github": "GitHub", "dpaste": "Dpaste", "pastecode": "PasteCode", "gitlab": "GitLab", "ideone": "Ideone", "pastegg": "paste.gg"}
        for name, raw, pw, sec in rows:
            online = source_is_online(name)
            _, last_str = get_last_crawled(name)
            sources.append({
                "name": name,
                "display": display_map.get(name, name),
                "icon": icon_map.get(name, ""),
                "raw": raw, "pw": pw, "sec": sec,
                "online": online,
                "last": last_str,
            })
        top_types = [{"label": lab, "count": cnt} for lab, cnt in collect_top_types(10)]
        recent = [{"ts": mtime, "source": s, "label": l} for mtime, s, l, _ in collect_recent(10)]
        data = json.dumps({
            "totals": {"raw": totals["raw"], "pw": totals["passwords"], "sec": totals["sensitive"]},
            "sources": sources,
            "top": top_types,
            "recent": recent,
            "pio": pio,
        })
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(data.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(data.encode("utf-8"))


class _SSLServer(socketserver.ThreadingTCPServer):
    """ThreadingTCPServer that wraps each client connection with SSL individually.

    Unlike wrapping the server socket with SSL, this ensures accept() never blocks
    on a stuck TLS handshake — each connection gets its own 5-second timeout.
    """
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, addr, handler, cert):
        super().__init__(addr, handler)
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(cert)
        self._ssl_ctx = ctx

    def get_request(self):
        sock, addr = self.socket.accept()
        sock.settimeout(5)
        try:
            return self._ssl_ctx.wrap_socket(sock, server_side=True), addr
        except (ssl.SSLError, OSError) as e:
            sock.close()
            raise OSError("SSL handshake failed")


cert = "logs/dashboard.pem"
if not os.path.exists(cert):
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048", "-keyout", cert,
        "-out", cert, "-days", "3650", "-nodes",
        "-subj", "/CN=localhost",
    ], capture_output=True)

httpd = _SSLServer((HOST, PORT), Handler, cert)

print("dashboard: https://" + HOST + ":" + str(PORT))
try:
    while True:
        httpd.handle_request()
except KeyboardInterrupt:
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print("\n" + ts + " shutting down dashboard...")
    httpd.server_close()
    sys.exit(0)