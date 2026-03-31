# Photo Progress Reporter (One-Click Local)

Creates monthly photo progress PDFs that follow your rules:
- No report title/month inside the PDF
- Filename format: `SITE - Mon YYYY.pdf`
- Each page: 1 photo + **timestamp only OVERLAID on the photo (top-left)**

## Folder layout

```
Input/
  Jan 2026/
    TPE Tampines/
    TPE Pasir Ris/
    PIE Simei/
    PIE Tampines/
```

## Install (first time only)

### Windows
Open PowerShell in this folder and run:
```
py -m pip install -r requirements.txt
```

### macOS
```
pip3 install -r requirements.txt
```

## One-click run
- Windows: double-click `run_windows.bat`
- macOS: double-click `run_mac.command`

## Changing the month
Edit the run file and update:
- MONTH
- INPUT folder

## Timestamp extraction
The script tries:
1) EXIF DateTimeOriginal (fast, best)
2) OCR (top-left overlay) using pytesseract + Tesseract (fallback)

If OCR is needed, install Tesseract:
- Windows: install Tesseract OCR, then `py -m pip install pytesseract`
- macOS: `brew install tesseract` then `pip3 install pytesseract`
