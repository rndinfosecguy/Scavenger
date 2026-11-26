import argparse
import os
import ssl
import subprocess
import sys
import time
import urllib.request

# Each entry: (flag_letter, long_name, script, tmux_session, help_text, source)
SCRAPERS = [
    ("a", "pastebin-archive", "scrapers/scraper_pastebin_archive.py", "s-pastebin-archive",
     "Pastebin archive scrape module", "pastebin"),
    ("t", "pastebin-track",   "scrapers/scraper_pastebin_track.py",   "s-pastebin-track",
     "Pastebin user track module", "pastebin"),
    ("p", "pastesio",         "scrapers/scraper_pastesio.py",         "s-pastesio",
     "Pastes.io random-ID scraper", "pastesio"),
    ("g", "github",           "scrapers/scraper_github.py",           "s-github",
     "GitHub gist scraper", "github"),
    ("d", "dpaste",           "scrapers/scraper_dpaste.py",           "s-dpaste",
     "Dpaste.com scraper", "dpaste"),
    ("c", "pastecode",        "scrapers/scraper_pastecode.py",        "s-pastecode",
     "Pastecode.io scraper", "pastecode"),
    ("l", "gitlab",           "scrapers/scraper_gitlab.py",           "s-gitlab",
     "GitLab snippet scraper", "gitlab"),
    ("i", "ideone",           "scrapers/scraper_ideone.py",           "s-ideone",
     "Ideone.com recent codes scraper", "ideone"),
    ("s", "pastegg",          "scrapers/scraper_pastegg.py",          "s-pastegg",
     "paste.gg API scraper", "pastegg"),
]

UTILITIES = [
    ("D", "dashboard",  "dashboard.py", "s-dashboard",
     "Web dashboard (HTTPS 127.0.0.1:8080, auto-refresh 60s)"),
]

EDITORS = [
    ("e", "edit-search", "configs/searchterms.txt",
     "Edit search terms file"),
    ("u", "edit-users",  "configs/users.txt",
     "Edit tracked users file"),
]

YEAR_SECONDS = 365 * 86400
DASHBOARD_URL = "https://127.0.0.1:8080/"


def _help_text(flag, items):
    for item in items:
        if item[0] == flag:
            return item[4] if len(item) > 4 else item[-1]
    return ""


def _build_panel_lines():
    lines = ["", "  SCRAPERS"]
    for flag, name, *_ in SCRAPERS:
        lines.append("  -" + flag + ", --" + name + "  " + _help_text(flag, SCRAPERS))
    lines.append("")
    lines.append("  UTILITIES")
    for flag, name, *_ in UTILITIES:
        lines.append("  -" + flag + ", --" + name + "  " + _help_text(flag, UTILITIES))
    lines.append("")
    lines.append("  EDITORS  (cannot be combined with other flags)")
    for flag, name, *_ in EDITORS:
        lines.append("  -" + flag + ", --" + name + "  " + _help_text(flag, EDITORS))
    lines.append("")
    lines.append("  CONTROL")
    lines.append("  --status   show tmux and last-crawl state")
    lines.append("  --stop     stop selected sessions (no flags = all)")
    lines.append("  --restart  restart selected sessions (no flags = all)")
    lines.append("  --version  print version")
    lines.append("")
    lines.append("  python3 scavenger.py -a -t  (combine flags)")
    return lines


def _show_panel():
    from classes.utility import panel
    panel("scavenger", *_build_panel_lines(), width=80)


def _build_parser():
    parser = argparse.ArgumentParser(
        description="multi-source credential-leak crawler control script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    for flag, name, *_ in SCRAPERS:
        parser.add_argument("-" + flag, "--" + name,
                            help=_help_text(flag, SCRAPERS), action="store_true")
    for flag, name, *_ in UTILITIES:
        parser.add_argument("-" + flag, "--" + name,
                            help=_help_text(flag, UTILITIES), action="store_true")
    for flag, name, *_ in EDITORS:
        parser.add_argument("-" + flag, "--" + name,
                            help=_help_text(flag, EDITORS) + " (cannot combine)",
                            action="store_true")
    control = parser.add_mutually_exclusive_group()
    control.add_argument("--status", action="store_true",
                         help="Show tmux session and last-crawl state")
    control.add_argument("--stop", action="store_true",
                         help="Stop selected sessions (no flags = all)")
    control.add_argument("--restart", action="store_true",
                         help="Restart selected sessions (no flags = all)")
    control.add_argument("--version", action="store_true",
                         help="Print the Scavenger version")
    return parser


def _session_state(session_name):
    """Return True/False for running/stopped, or None if tmux is unavailable."""
    try:
        result = subprocess.run(["tmux", "has-session", "-t", session_name],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        return None
    return result.returncode == 0


def _dashboard_online(timeout=2):
    """Return True if the dashboard responds over HTTPS with a successful status."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(DASHBOARD_URL, timeout=timeout, context=context) as response:
            return 200 <= response.status < 400
    except Exception:
        return False


def _start_tmux(session_name, script_file, module_name):
    from classes.utility import log
    state = _session_state(session_name)
    if state is True:
        log("WARN", module_name + " already running  [" + session_name + "]")
        return True
    if state is None:
        log("ERROR", "tmux not installed - cannot launch " + module_name)
        return False
    repo_root = os.path.dirname(os.path.abspath(__file__))
    try:
        result = subprocess.run(["tmux", "new", "-d", "-s", session_name,
                                 "cd " + repo_root + " && python3 " + script_file],
                                capture_output=True, text=True)
    except FileNotFoundError:
        log("ERROR", "tmux not installed - cannot launch " + module_name)
        return False
    if result.returncode != 0:
        log("ERROR", "failed to launch " + module_name + ": " + result.stderr.strip())
        return False
    log("OK", "launched " + module_name + "  [" + session_name + "]")
    return True


def _stop_tmux(session_name, module_name):
    from classes.utility import log
    state = _session_state(session_name)
    if state is None:
        log("ERROR", "tmux not installed - cannot stop " + module_name)
        return False
    if not state:
        log("INFO", module_name + " already stopped  [" + session_name + "]")
        return True
    try:
        result = subprocess.run(["tmux", "kill-session", "-t", session_name],
                                capture_output=True, text=True)
    except FileNotFoundError:
        log("ERROR", "tmux not installed - cannot stop " + module_name)
        return False
    if result.returncode != 0:
        log("ERROR", "failed to stop " + module_name + ": " + result.stderr.strip())
        return False
    log("OK", "stopped " + module_name + "  [" + session_name + "]")
    return True


def _read_version():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION")
    try:
        with open(path) as f:
            return f.read().strip() or "unknown"
    except OSError:
        return "unknown"


def _read_last_crawled(source):
    if not source:
        return 0
    try:
        with open("logs/" + source + "_last_crawled.txt") as f:
            return float(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def _format_age(ts):
    if not ts:
        return "never"
    elapsed = time.time() - ts
    if elapsed < 60:
        return "just now"
    if elapsed < 3600:
        return str(int(elapsed // 60)) + "m ago"
    if elapsed < 86400:
        return str(int(elapsed // 3600)) + "h " + str(int((elapsed % 3600) // 60)) + "m ago"
    if elapsed < YEAR_SECONDS:
        return str(int(elapsed // 86400)) + "d " + str(int((elapsed % 86400) // 3600)) + "h ago"
    return str(int(elapsed // YEAR_SECONDS)) + "y " + str(int((elapsed % YEAR_SECONDS) // 86400)) + "d ago"


def _session_records():
    records = []
    for flag, name, script, session, _help_text, source in SCRAPERS:
        records.append({"flag": flag, "name": name, "script": script,
                        "session": session, "source": source})
    for flag, name, script, session, _help_text in UTILITIES:
        records.append({"flag": flag, "name": name, "script": script,
                        "session": session, "source": None})
    return records


def _selected_sessions(args):
    records = _session_records()
    selected = [r for r in records if getattr(args, r["name"].replace("-", "_"))]
    return selected or records


def _show_status(records):
    from classes.utility import panel
    now = time.time()
    rows = []
    for rec in records:
        source = rec["source"]
        tmux = _session_state(rec["session"])
        tmux_str = "unknown" if tmux is None else ("running" if tmux else "stopped")
        if source:
            ts = _read_last_crawled(source)
            last = _format_age(ts)
            state = "online" if ts and (now - ts) < 3600 else "offline"
        elif rec["name"] == "dashboard":
            last = "-"
            if tmux is True:
                state = "online" if _dashboard_online() else "unreachable"
            elif tmux is False:
                state = "offline"
            else:
                state = "unknown"
        else:
            last = "-"
            state = "-"
        rows.append((rec["name"], "-" + rec["flag"], rec["session"], tmux_str, last, state))

    headers = ("module", "flag", "session", "tmux", "last crawl", "state")
    widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(6)]
    lines = ["  ".join(str(row[i]).ljust(widths[i]) for i in range(6))
             for row in [headers] + rows]
    panel("scavenger status", *lines, width=sum(widths) + 2 * (len(widths) - 1) + 4)


def _start_sessions(records):
    ok = True
    for rec in records:
        if not _start_tmux(rec["session"], rec["script"], rec["name"]):
            ok = False
    return ok


def _stop_sessions(records):
    ok = True
    for rec in records:
        if not _stop_tmux(rec["session"], rec["name"]):
            ok = False
    return ok


def _edit_file(filepath, label):
    from classes.utility import log
    subprocess.run(["vi", filepath])
    if label == "edit-search":
        _validate_search_terms()
    log("WARN", label + " changed - will be picked up automatically on the next pass")


def _validate_search_terms():
    """Check searchterms.txt for entries that may cause noise."""
    from classes.utility import log, PRECISE_PATTERNS
    warnings = []
    try:
        for line in open("configs/searchterms.txt"):
            line = line.strip()
            if not line:
                continue
            if len(line) <= 3:
                warnings.append(f"  '{line}' — too short, likely false positives")
            for name, _ in PRECISE_PATTERNS:
                if line.lower() in name.lower():
                    warnings.append(f"  '{line}' — overlaps with precise pattern '{name}'")
    except FileNotFoundError:
        return
    if warnings:
        log("WARN", "potential issues in searchterms.txt:")
        for w in warnings:
            log("WARN", w)
    else:
        log("OK", "no issues found in searchterms.txt")


def _collect_flags(args, items):
    return {getattr(args, name.replace("-", "_")) for _, name, *_ in items}


def main():
    parser = _build_parser()
    args = parser.parse_args()

    scraper_flags = _collect_flags(args, SCRAPERS)
    utility_flags = _collect_flags(args, UTILITIES)
    editor_flags = _collect_flags(args, EDITORS)

    any_scraper = any(scraper_flags)
    any_utility = any(utility_flags)
    any_editor = any(editor_flags)
    operation = ("status" if args.status else
                 "stop" if args.stop else
                 "restart" if args.restart else None)

    if args.version:
        if any_scraper or any_utility or any_editor or operation:
            from classes.utility import log
            log("ERROR", "--version cannot be used with other arguments")
            sys.exit(1)
        print(_read_version())
        sys.exit(0)

    if not (any_scraper or any_utility or any_editor or operation):
        _show_panel()
        sys.exit(0)

    # Editors cannot be combined with other flags
    if any_editor and (any_scraper or any_utility or operation):
        from classes.utility import log
        for flag, name, *_ in EDITORS:
            if getattr(args, name.replace("-", "_")):
                log("ERROR", "-" + flag + "/--" + name + " cannot be used with other arguments")
        sys.exit(1)

    if operation:
        records = _selected_sessions(args)
        if operation == "status":
            _show_status(records)
            return
        ok = _stop_sessions(records)
        if operation == "restart":
            ok = _start_sessions(records) and ok
        sys.exit(0 if ok else 1)

    # Start scrapers
    ok = True
    for flag, name, script, session, *_ in SCRAPERS:
        if getattr(args, name.replace("-", "_")):
            ok = _start_tmux(session, script, name) and ok

    # Start utilities
    for flag, name, script, session, *_ in UTILITIES:
        if getattr(args, name.replace("-", "_")):
            ok = _start_tmux(session, script, name) and ok

    # Run editors
    for flag, name, filepath, *_ in EDITORS:
        if getattr(args, name.replace("-", "_")):
            _edit_file(filepath, name)

    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
