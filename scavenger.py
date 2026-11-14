import argparse
import subprocess
import sys

# Each entry: (flag_letter, long_name, script, tmux_session, help_text)
SCRAPERS = [
    ("a", "pastebin-archive", "scraper_pastebin_archive.py", "s-pastebin-archive",
     "Pastebin archive scrape module"),
    ("t", "pastebin-track",   "scraper_pastebin_track.py",   "s-pastebin-track",
     "Pastebin user track module"),
    ("p", "pastesio",         "scraper_pastesio.py",         "s-pastesio",
     "Pastes.io random-ID scraper"),
    ("g", "github",           "scraper_github.py",           "s-github",
     "GitHub gist scraper"),
    ("d", "dpaste",           "scraper_dpaste.py",           "s-dpaste",
     "Dpaste.com scraper"),
    ("c", "pastecode",        "scraper_pastecode.py",        "s-pastecode",
     "Pastecode.io scraper"),
    ("l", "gitlab",           "scraper_gitlab.py",           "s-gitlab",
     "GitLab snippet scraper"),
]

UTILITIES = [
    ("D", "dashboard",  "dashboard.py", "s-dashboard",
     "Web dashboard (HTTPS 127.0.0.1:8080, auto-refresh 30s)"),
]

EDITORS = [
    ("e", "edit-search", "configs/searchterms.txt",
     "Edit search terms file"),
    ("u", "edit-users",  "configs/users.txt",
     "Edit tracked users file"),
]


def _help_text(flag, items):
    for item in items:
        if item[0] == flag:
            return item[-1]
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
    lines.append("  EDITORS  (cannot combine with other flags)")
    for flag, name, *_ in EDITORS:
        lines.append("  -" + flag + ", --" + name + "  " + _help_text(flag, EDITORS))
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
    return parser


def _start_tmux(session_name, script_file):
    from classes.utility import log
    log("OK", "starting " + script_file + " in detached tmux session `" + session_name + "`")
    subprocess.run(["tmux", "new", "-d", "-s", session_name,
                    "python3 " + script_file])


def _edit_file(filepath, label):
    from classes.utility import log
    subprocess.run(["vi", filepath])
    log("WARN", label + " changed - restart the affected module")


def _collect_flags(args, items):
    return {getattr(args, name.replace("-", "_")) for _, name, *_ in items}


def main():
    _show_panel()
    parser = _build_parser()
    args = parser.parse_args()

    scraper_flags = _collect_flags(args, SCRAPERS)
    utility_flags = _collect_flags(args, UTILITIES)
    editor_flags = _collect_flags(args, EDITORS)

    any_scraper = any(scraper_flags)
    any_utility = any(utility_flags)
    any_editor = any(editor_flags)

    if not (any_scraper or any_utility or any_editor):
        parser.print_help()
        sys.exit(0)

    # Editors cannot be combined with anything
    if any_editor and (any_scraper or any_utility):
        from classes.utility import log
        for flag, name, *_ in EDITORS:
            if getattr(args, name.replace("-", "_")):
                log("ERROR", "-" + flag + "/--" + name + " cannot be used with other arguments")
        sys.exit(1)

    # Start scrapers
    for flag, name, script, session, *_ in SCRAPERS:
        if getattr(args, name.replace("-", "_")):
            _start_tmux(session, script)

    # Start utilities
    for flag, name, script, session, *_ in UTILITIES:
        if getattr(args, name.replace("-", "_")):
            _start_tmux(session, script)

    # Run editors
    for flag, name, filepath, *_ in EDITORS:
        if getattr(args, name.replace("-", "_")):
            _edit_file(filepath, name)


if __name__ == "__main__":
    main()