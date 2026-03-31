#!/bin/bash
set -e

# ---- EDIT THESE TWO LINES ----
MONTH="Jan 2026"
INPUT="Input/Jan 2026"
# ------------------------------

if [ ! -d "$INPUT" ]; then
  echo "Input folder not found: $INPUT"
  read -p "Press enter to exit..."
  exit 1
fi

python3 make_reports.py --input "$INPUT" --month "$MONTH" --output "Output" --strict
echo ""
read -p "Done. Press enter to exit..."
