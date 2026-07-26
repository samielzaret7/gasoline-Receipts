# Gasoline Receipts

Fetches Journie gas station receipts from Gmail and converts them to PDFs, organized by month.

## How It Works

1. Queries Gmail for unread emails from `journiehelp@artisoftlabs.com`
2. Parses the HTML email body using [gmail-utils](https://github.com/samielzaret7/gmail-utils)
3. Extracts the date from the email's `Date` header
4. Converts each email to a PDF using WeasyPrint
5. Saves PDFs to `RECEIPTS_FOLDER/MONTH/Gasoline - MONTH DD.pdf`
6. Marks emails as read after successful processing

## Setup

On a fresh machine, run:

```bash
./setup.sh
```

That installs the native libraries WeasyPrint needs, creates `.venv`, and installs
the Python packages. It is idempotent — re-run it any time.

Then, one time only:

1. **Google OAuth:** Place your `credentials.json` in this directory. On first run, the script opens a browser for OAuth consent and saves `token.json`.

2. **Environment variables:** Copy `.env.example` to `.env` and set your receipts folder path:
   ```bash
   cp .env.example .env
   ```

### Why not just `pip install -r requirements.txt`?

Because it cannot work on its own. WeasyPrint doesn't bundle a rendering engine —
it loads the Pango, cairo and GLib **C** libraries at import time. Those aren't
Python packages and aren't on PyPI, so no `pip` command can supply them.
Homebrew is the practical way to get them on macOS.

`setup.sh` exists so that this is one command instead of an afternoon.

## Usage

```bash
./run_gasoline_receipts.command
```

Or manually:

```bash
source .venv/bin/activate && python journie_receipts_to_pdf.py
```

Logs are written to `logs/YYYY-MM-DD/` with auto-incrementing filenames per run.

## Troubleshooting

Both failures below were hit during a machine rebuild. `setup.sh` prevents both;
this section records *why*, so the debugging doesn't have to be repeated.

### `Failed to build installable wheels ... cryptography`

**Cause: an outdated `pip`, not a missing compiler.**

`cryptography` (pulled in by `google-auth`) ships prebuilt macOS wheels. macOS's
built-in `/usr/bin/python3` carries a pip from 2021 that fails to match those
wheels and falls back to compiling from source — which then demands Rust and
OpenSSL headers.

The fix is to upgrade pip *before* installing anything, which `setup.sh` does:

```bash
python3 -m pip install --upgrade pip setuptools wheel
```

Installing `rust`, `openssl` and `pkg-config` also makes the error go away, by
letting the source build succeed. That works, but it's treating the symptom —
none of those are needed once pip can find the wheel.

Also make sure you are not using `/usr/bin/python3`: it is Python 3.9, and
`gmail-utils` requires 3.10+. `setup.sh` skips it automatically.

### `OSError: cannot load library 'libgobject-2.0-0'`

**Cause: genuinely missing system libraries.** This one really does need Homebrew.

```bash
brew install pango
```

`pango` pulls in cairo, GLib, HarfBuzz and fontconfig as dependencies, which
covers everything WeasyPrint looks for — installing them individually isn't
necessary.

### Note on Homebrew and Python

Homebrew installs its own `python@3.14` as a dependency of other formulae. It is
**not** used by this project and does not conflict with anything. `.venv` is
built from whichever Python you ran `setup.sh` with (check `.venv/pyvenv.cfg`),
and the only thing Homebrew contributes here are the `.dylib` files in
`/usr/local/lib` that WeasyPrint loads at runtime.

## Dependencies

- [gmail-utils](https://github.com/samielzaret7/gmail-utils) — Gmail API authentication and email parsing
- [WeasyPrint](https://weasyprint.org/) — HTML to PDF conversion
- [python-dotenv](https://github.com/theskumar/python-dotenv) — `.env` file loading
