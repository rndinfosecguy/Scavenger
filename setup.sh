#!/bin/bash
# Scavenger setup.
# Installs Python packages and required system tools, removes the placeholder
# README files, and ensures every data storage folder exists.
# Idempotent: safe to re-run at any time.
set -u

# Every script in this repo hardcodes relative paths — run from the repo root.
cd "$(dirname "$0")" || exit 1

SOURCES="pastebin pastesio github dpaste pastecode"
DIRS="data data/raw_pastes data/files_with_passwords data/otherSensitivePastes archive logs"
for s in $SOURCES; do
    DIRS="$DIRS data/raw_pastes/$s data/files_with_passwords/$s data/otherSensitivePastes/$s"
done

# ------------------------------------------------------------- system tools

sudo_if_needed() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
    else
        sudo "$@"
    fi
}

detect_pkg_manager() {
    for m in apt-get dnf yum pacman apk brew; do
        if command -v "$m" >/dev/null 2>&1; then
            echo "$m"
            return 0
        fi
    done
    echo "none"
}

PKG_MANAGER="$(detect_pkg_manager)"
case "$PKG_MANAGER" in
    apt)     PKG_PYTHON="python3";     PKG_PIP="python3-pip"; PKG_EDITOR="vim-tiny"    ;;
    dnf)     PKG_PYTHON="python3";     PKG_PIP="python3-pip"; PKG_EDITOR="vim-minimal" ;;
    yum)     PKG_PYTHON="python3";     PKG_PIP="python3-pip"; PKG_EDITOR="vim-minimal" ;;
    pacman)  PKG_PYTHON="python3";     PKG_PIP="python-pip";  PKG_EDITOR="vim"         ;;
    apk)     PKG_PYTHON="python3";     PKG_PIP="py3-pip";     PKG_EDITOR="vim"         ;;
    brew)    PKG_PYTHON="python3";     PKG_PIP="";            PKG_EDITOR="vim"         ;;
    none)
        echo "ERROR: no supported package manager found (apt-get/dnf/yum/pacman/apk/brew)."
        echo "       Install python3, pip, tmux, an editor (vi/vim) and openssl manually, then re-run this script."
        exit 1
        ;;
esac

install_pkg() {
    case "$PKG_MANAGER" in
        apt)    sudo_if_needed apt-get install -y "$1" ;;
        dnf)    sudo_if_needed dnf install -y "$1" ;;
        yum)    sudo_if_needed yum install -y "$1" ;;
        pacman) sudo_if_needed pacman -S --noconfirm "$1" ;;
        apk)    sudo_if_needed apk add "$1" ;;
        brew)   brew install "$1" ;;
    esac
}

echo "==> System tools"
MISSING_PKGS=""

if command -v python3 >/dev/null 2>&1; then
    echo "OK   python3"
else
    echo "MISS python3 (package: $PKG_PYTHON)"
    MISSING_PKGS="$MISSING_PKGS $PKG_PYTHON"
fi

if python3 -m pip --version >/dev/null 2>&1; then
    echo "OK   pip"
else
    if [ -n "$PKG_PIP" ]; then
        echo "MISS pip (package: $PKG_PIP)"
        MISSING_PKGS="$MISSING_PKGS $PKG_PIP"
    else
        echo "MISS pip — python3 on this platform should bundle it"
        MISSING_PKGS="$MISSING_PKGS $PKG_PYTHON"
    fi
fi

if command -v tmux >/dev/null 2>&1; then
    echo "OK   tmux"
else
    echo "MISS tmux (package: tmux)"
    MISSING_PKGS="$MISSING_PKGS tmux"
fi

if command -v vi >/dev/null 2>&1 || command -v vim >/dev/null 2>&1; then
    echo "OK   vi/vim"
else
    echo "MISS vi/vim (package: $PKG_EDITOR)"
    MISSING_PKGS="$MISSING_PKGS $PKG_EDITOR"
fi

if command -v openssl >/dev/null 2>&1; then
    echo "OK   openssl"
else
    echo "MISS openssl (package: openssl)"
    MISSING_PKGS="$MISSING_PKGS openssl"
fi

if [ -n "$MISSING_PKGS" ]; then
    if [ "$PKG_MANAGER" = "apt" ]; then
        echo "==> refreshing apt metadata (apt-get update)"
        sudo_if_needed apt-get update -qq
    fi
    for pkg in $MISSING_PKGS; do
        echo "==> installing $pkg"
        if ! install_pkg "$pkg"; then
            echo "ERROR: failed to install '$pkg' — install it manually, then re-run this script."
            exit 1
        fi
    done
else
    echo "OK   all system tools already present"
fi

# --------------------------------------------------------- python packages

echo
echo "==> Python packages (requirements.txt)"
PIP_OUT="$(python3 -m pip install -r requirements.txt 2>&1)"
PIP_RC=$?
if [ "$PIP_RC" -ne 0 ] && printf '%s\n' "$PIP_OUT" | grep -qi "externally-managed-environment"; then
    echo "INFO: system Python is externally managed (PEP 668) — retrying with --break-system-packages"
    PIP_OUT="$(python3 -m pip install --break-system-packages -r requirements.txt 2>&1)"
    PIP_RC=$?
fi
if [ "$PIP_RC" -ne 0 ]; then
    echo "ERROR: pip install failed:"
    printf '%s\n' "$PIP_OUT"
    echo "HINT: install manually with: python3 -m pip install -r requirements.txt"
    exit 1
fi
echo "OK   Python packages installed"

# --------------------------------------------------------- placeholder READMEs

echo
echo "==> Removing placeholder README files"
REMOVED=0
while IFS= read -r f; do
    if grep -q "Delete this file before you start the bot." "$f" 2>/dev/null; then
        rm -f "$f"
        echo "removed: $f"
        REMOVED=$((REMOVED + 1))
    fi
done < <(find data archive -name README.md -type f 2>/dev/null)
if [ "$REMOVED" -gt 0 ]; then
    echo "OK   removed $REMOVED placeholder file(s)"
else
    echo "OK   no placeholder README files found"
fi

# ------------------------------------------------------------- storage folders

echo
echo "==> Ensuring storage folders exist"
CREATED=0
for d in $DIRS; do
    if [ ! -d "$d" ]; then
        mkdir -p "$d"
        echo "created: $d/"
        CREATED=$((CREATED + 1))
    fi
done
if [ "$CREATED" -gt 0 ]; then
    echo "OK   created $CREATED folder(s)"
else
    echo "OK   all storage folders already present"
fi

echo
echo "=============================================="
echo "Scavenger setup complete."
echo "Next: python3 scavenger.py -h"