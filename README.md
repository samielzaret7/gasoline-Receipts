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

1. **Google OAuth:** Place your `credentials.json` in this directory. On first run, the script opens a browser for OAuth consent and saves `token.json`.

2. **Environment variables:** Copy `.env.example` to `.env` and set your receipts folder path:
   ```bash
   cp .env.example .env
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python journie_receipts_to_pdf.py
```

Logs are written to `logs/YYYY-MM-DD/` with auto-incrementing filenames per run.

## Dependencies

- [gmail-utils](https://github.com/samielzaret7/gmail-utils) — Gmail API authentication and email parsing
- [WeasyPrint](https://weasyprint.org/) — HTML to PDF conversion
- [python-dotenv](https://github.com/theskumar/python-dotenv) — `.env` file loading
