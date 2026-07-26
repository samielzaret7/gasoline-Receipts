"""
journie_receipts_to_pdf.py

- Fetches unread Journie receipts from Gmail
- Uses gmail-utils (shared module)
- Converts each email (HTML) to a PDF
- Organizes PDFs by month
- Marks emails as READ immediately after successful parsing

Logging:
- Creates logs/YYYY-MM-DD/ folder under working directory
- Writes per-run log file: GasolineReceiptsLog_1.log, GasolineReceiptsLog_2.log, ...
"""

import os
import logging
from datetime import date
from typing import List, Dict

from dotenv import load_dotenv
from email.utils import parsedate_to_datetime

try:
    from weasyprint import HTML
except OSError as exc:  # Pango/cairo/GLib are missing — pip cannot install these
    raise SystemExit(
        f"WeasyPrint could not load its native libraries ({exc}).\n"
        "Fix it by running ./setup.sh, or directly with: brew install pango"
    ) from exc

from gmail_utils import get_email_items_main


# -----------------------
# Configuration
# -----------------------

QUERY = "from:journiehelp@artisoftlabs.com is:unread"
FORMAT = "full"  # Journie emails are best parsed via FULL payload
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

load_dotenv(".env")
RECEIPTS_FOLDER = os.getenv("RECEIPTS_FOLDER")


# -----------------------
# Logging setup (per-run file)
# -----------------------

def _next_log_file_path(base_dir: str, prefix: str) -> str:
    """
    Creates logs/YYYY-MM-DD/ and returns the next available log filename:
    GasolineReceiptsLog_1.log, GasolineReceiptsLog_2.log, ...
    """
    today = str(date.today())
    day_dir = os.path.join(base_dir, "logs", today)
    os.makedirs(day_dir, exist_ok=True)

    n = 1
    while True:
        candidate = os.path.join(day_dir, f"{prefix}_{n}.log")
        if not os.path.exists(candidate):
            return candidate
        n += 1


def setup_logging() -> str:
    """
    Sets up logging to a per-run file (and optionally console).
    Returns the log file path.
    """
    # Important if you run multiple times in the same Python session
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    cwd = os.getcwd()
    log_file = _next_log_file_path(cwd, "GasolineReceiptsLog")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] - %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode="w", encoding="utf-8"),
            logging.StreamHandler(),  # keep console output; remove if you only want file
        ],
    )

    logging.info("Logging initialized. log_file=%s", log_file)
    return log_file


# -----------------------
# Helpers
# -----------------------

def safe_filename(base_path: str) -> str:
    """Ensures we don't overwrite an existing PDF."""
    if not os.path.exists(base_path):
        return base_path

    counter = 1
    name, ext = os.path.splitext(base_path)
    while True:
        candidate = f"{name}_{counter}{ext}"
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def parse_email_date(raw_date: str) -> tuple[str | None, str | None]:
    """
    Parses the RFC 2822 Date header from Gmail and returns (MONTH, DAY).
    Example: "Tue, 26 Dec 2025 09:41:22 -0500"
    """
    if not raw_date:
        return None, None

    try:
        parsed = parsedate_to_datetime(raw_date)
        month = parsed.strftime("%B").upper()
        day = parsed.strftime("%d")
        return month, day
    except Exception:
        return None, None


# -----------------------
# Main processing
# -----------------------

def process_receipts():
    logging.info("Starting Journie receipt ingestion")

    if not RECEIPTS_FOLDER:
        raise RuntimeError("RECEIPTS_FOLDER is not set in .env")

    os.makedirs(RECEIPTS_FOLDER, exist_ok=True)

    items: List[Dict[str, str]] = get_email_items_main(
        SCOPES=SCOPES,
        query=QUERY,
        format=FORMAT,
        body_preference=("html", "plain"),
        mark_as_read=True,  # immediate marking is OK for this project
        logger=logging.getLogger(__name__),
    )

    logging.info("Emails fetched: %s", len(items))
    print(f"Emails fetched: {len(items)}")

    for item in items:
        html_body = item.get("Body", "")
        raw_date = item.get("EmailDate", "")

        month, day = parse_email_date(raw_date)

        if month and day:
            month_dir = os.path.join(RECEIPTS_FOLDER, month)
            os.makedirs(month_dir, exist_ok=True)
            file_path = os.path.join(month_dir, f"Gasoline - {month} {day}.pdf")
        else:
            file_path = os.path.join(RECEIPTS_FOLDER, "Gasoline - Unable to Parse Date.pdf")

        file_path = safe_filename(file_path)

        try:
            HTML(string=html_body).write_pdf(target=file_path)
            logging.info("PDF written: %s", file_path)
            print(f"Saved: {file_path}")
        except Exception:
            logging.exception("Failed to write PDF. message_id=%s", item.get("gmail_message_id"))

    logging.info("Journie receipt ingestion finished")


# -----------------------
# Entry point
# -----------------------

if __name__ == "__main__":
    log_file = setup_logging()
    print(f"Log file: {log_file}")
    process_receipts()

