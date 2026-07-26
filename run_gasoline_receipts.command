#!/bin/bash

# 1. Automatically switch to the directory where this script lives
cd "$(dirname "$0")"

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Run your Python script
python3 journie_receipts_to_pdf.py

# 4. Deactivate the environment (Optional)
deactivate
