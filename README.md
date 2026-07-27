https://flare-ccecc-monthly-report-generato.vercel.app

# Photo Progress Reporter (Web + One-Click Local)

Creates monthly photo progress PDFs that follow your rules:
- No report title/month inside the PDF
- Filename format: `SITE - Mon YYYY.pdf`
- Each page: 1 photo + **timestamp only OVERLAID on the photo (top-left)**
- The hosted app automatically sorts unsorted original photos into the four CCECC sites using EXIF GPS metadata

## Recommended: hosted browser app

Open <https://flare-ccecc-monthly-report-generato.vercel.app>.

1. Select all the raw photo files together, or select one folder containing the raw photos.
2. Enter the month label, for example `Jan 2026`.
3. Review the automatic GPS sorting preview for:
   - TPE Pasir Ris
   - TPE Tampines
   - PIE Tampines
   - PIE Simei
4. Resolve any photo shown under **Needs review**, or turn off strict mode to skip it.
5. Click **Generate PDFs** and save the ZIP download.

No site folders or manual sorting are required. Processing stays in the browser and the selected photos are not uploaded to an application server.

### GPS classification safeguards

The app assigns each photo to the nearest supplied site pin. It flags a photo for review instead of guessing when:

- GPS metadata is missing or invalid.
- The closest site pin is more than 750 m away.
- The closest and second-closest site matches differ by less than 20 m.

Use original camera or drone files. Messaging and photo-sharing apps may remove EXIF GPS metadata.

## Optional: local Python web GUI

The local Python web GUI retains the legacy site-folder workflow.

- Windows: double-click `run_web_windows.bat`
- macOS: double-click `run_web_mac.command`

The launcher installs the needed Python packages automatically, then your browser opens `http://127.0.0.1:5000`.

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
