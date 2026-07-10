# Photo Progress Reporter (Web + One-Click Local)

Creates monthly photo progress PDFs that follow your rules:
- No report title/month inside the PDF
- Filename format: `SITE - Mon YYYY.pdf`
- Each page: 1 photo + **timestamp only OVERLAID on the photo (top-left)**

## Recommended: browser-based GUI

Use the web GUI if you do not want to edit files or run command-line commands.

### Start the web GUI

- Windows: double-click `run_web_windows.bat`
- macOS: double-click `run_web_mac.command`

The launcher installs the needed Python packages automatically, then your browser will open `http://127.0.0.1:5000`.

### Use the web GUI

1. Prepare one month folder with one folder per site:
   ```
   Jan 2026/
     TPE Tampines/
       photo1.jpg
       photo2.jpg
     TPE Pasir Ris/
       photo1.jpg
   ```
2. In the browser, enter the month label, for example `Jan 2026`.
3. Click **Choose File** / **Choose Folder** and select the month folder.
4. Keep **Strict mode** on if every photo must have a timestamp.
5. Click **Generate PDF ZIP**.
6. Save and unzip the downloaded file to get the generated PDFs.

> Note: Folder upload is supported by modern Chrome, Edge, and Safari browsers. The web app runs locally on your computer at `127.0.0.1`; it does not upload photos to an external service.

## Desktop GUI

If you prefer selecting existing input and output folders on your computer:

- Windows: double-click `run_gui_windows.bat`
- macOS: double-click `run_gui_mac.command`

## Command-line / one-click legacy run

Folder layout:

```
Input/
  Jan 2026/
    TPE Tampines/
    TPE Pasir Ris/
    PIE Simei/
    PIE Tampines/
```

- Windows: double-click `run_windows.bat`
- macOS: double-click `run_mac.command`

To change the month for the legacy run, edit the run file and update:
- `MONTH`
- `INPUT` folder

## Timestamp extraction

The script tries:
1. EXIF DateTimeOriginal (fast, best)
2. OCR (top-left overlay) using pytesseract + Tesseract (fallback)

If OCR is needed, install Tesseract:
- Windows: install Tesseract OCR, then `py -m pip install pytesseract`
- macOS: `brew install tesseract` then `pip3 install pytesseract`
