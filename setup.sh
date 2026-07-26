#!/bin/bash
#
# One-command setup for gasolineReceipts.
#
# Run this after a fresh macOS install:
#
#     ./setup.sh
#
# It is idempotent — safe to re-run any time.
#
# Why this exists instead of a plain `pip install -r requirements.txt`:
# WeasyPrint does not bundle its rendering engine. It dlopen()s the Pango /
# cairo / GLib C libraries at import time, and those are not on PyPI, so pip
# alone can never install them. Homebrew is the only practical source on macOS.
# See the Troubleshooting section of README.md for the full story.

set -euo pipefail

cd "$(dirname "$0")"

MIN_PY_MINOR=10  # gmail-utils declares requires-python >=3.10

say()  { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
fail() { printf '\n\033[1;31mError:\033[0m %s\n' "$1" >&2; exit 1; }

# ---------------------------------------------------------------------------
# 1. Native libraries (Pango & friends) via Homebrew
# ---------------------------------------------------------------------------

say "Checking native libraries"

if ! command -v brew >/dev/null 2>&1; then
    fail "Homebrew is not installed, and WeasyPrint cannot work without it.

Install it, then re-run this script:

    /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"

(Not run automatically — it modifies system directories and asks for your password.)"
fi

# `pango` pulls in cairo, glib, harfbuzz and fontconfig as dependencies, which
# together cover every library WeasyPrint looks for. Installing them
# individually is unnecessary.
if brew list --formula pango >/dev/null 2>&1; then
    echo "pango already installed"
else
    brew install pango
fi

# ---------------------------------------------------------------------------
# 2. Pick a suitable Python
# ---------------------------------------------------------------------------

say "Selecting Python interpreter"

# macOS ships /usr/bin/python3 (currently 3.9) with a pip from 2021. Both the
# version and that ancient pip cause failures here, so skip it deliberately.
pick_python() {
    local candidate
    for candidate in \
        "$(command -v python3 || true)" \
        /Library/Frameworks/Python.framework/Versions/3.*/bin/python3 \
        /opt/homebrew/bin/python3 \
        /usr/local/bin/python3
    do
        [ -x "$candidate" ] || continue
        if "$candidate" -c "import sys; sys.exit(0 if sys.version_info[:2] >= (3, $MIN_PY_MINOR) else 1)" 2>/dev/null; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

PYTHON="$(pick_python)" || fail "No Python 3.$MIN_PY_MINOR+ found.

macOS's built-in /usr/bin/python3 is too old for this project.
Install a current Python from https://www.python.org/downloads/macos/
(or \`brew install python\`), then re-run this script."

echo "Using $PYTHON ($("$PYTHON" --version 2>&1))"

# ---------------------------------------------------------------------------
# 3. Virtual environment
# ---------------------------------------------------------------------------

say "Setting up virtual environment"

if [ -x .venv/bin/python ]; then
    echo ".venv already exists"
else
    "$PYTHON" -m venv .venv
    echo "created .venv"
fi

# ---------------------------------------------------------------------------
# 4. Python dependencies
# ---------------------------------------------------------------------------
#
# Upgrading pip FIRST is the important part. A stale pip fails to match the
# prebuilt `cryptography` wheels and falls back to compiling from source, which
# then demands a Rust toolchain and OpenSSL headers. With a current pip the
# wheel is downloaded and no compiler is involved at all.

say "Installing Python dependencies"

.venv/bin/python -m pip install --quiet --upgrade pip setuptools wheel
.venv/bin/python -m pip install -r requirements.txt

# ---------------------------------------------------------------------------
# 5. Verify
# ---------------------------------------------------------------------------

say "Verifying installation"

.venv/bin/python - <<'PY'
import weasyprint
import weasyprint.text.ffi  # forces the Pango/GLib libraries to load
from gmail_utils import get_email_items_main  # noqa: F401

print(f"WeasyPrint {weasyprint.__version__} + Pango loaded")
print("gmail-utils importable")
PY

say "Setup complete"

cat <<'EOF'
Remaining manual steps (only needed the first time):

  1. Put your Google OAuth `credentials.json` in this folder.
  2. cp .env.example .env   and set RECEIPTS_FOLDER.

Then run the project with:

  ./run_gasoline_receipts.command
EOF
