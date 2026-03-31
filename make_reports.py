#!/usr/bin/env python3
"""
Photo Progress Reporter (one-click local)

Creates site PDFs from folders of photos, placing each photo on its own page and
printing ONLY the timestamp (extracted from EXIF if available, otherwise OCR from top-left overlay).

Timestamp is OVERLAID on the photo (top-left), matching your requirement.

Folder layout example:
Input/
  Jan 2026/
    TPE Tampines/
      IMG_0001.jpg
      ...
    PIE Simei/
      ...

Outputs:
Output/
  TPE Tampines - Jan 2026.pdf
  PIE Simei - Jan 2026.pdf
  ...

Usage (CLI):
  python make_reports.py --input "Input/Jan 2026" --month "Jan 2026" --output "Output"
"""

from __future__ import annotations
import argparse
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from PIL import Image, ImageOps, ImageEnhance, ExifTags

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.units import mm

TIMESTAMP_REGEX = re.compile(r'(\d{4}[/-]\d{2}[/-]\d{2})\s+(\d{2}:\d{2}:\d{2})')
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}

def _parse_timestamp_str(s: str) -> Optional[datetime]:
    m = TIMESTAMP_REGEX.search(s)
    if not m:
        return None
    date_part = m.group(1).replace("-", "/")
    time_part = m.group(2)
    try:
        return datetime.strptime(f"{date_part} {time_part}", "%Y/%m/%d %H:%M:%S")
    except ValueError:
        return None

def _format_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y/%m/%d %H:%M:%S")

def extract_timestamp_exif(img: Image.Image) -> Optional[datetime]:
    """Try to extract DateTimeOriginal/DateTime from EXIF."""
    try:
        exif = img.getexif()
        if not exif:
            return None
        tag_map = {v: k for k, v in ExifTags.TAGS.items()}
        for key_name in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
            tag_id = tag_map.get(key_name)
            if tag_id and tag_id in exif:
                raw = str(exif.get(tag_id))
                # EXIF is usually "YYYY:MM:DD HH:MM:SS"
                raw = raw.replace(":", "/", 2)
                dt = _parse_timestamp_str(raw)
                if dt:
                    return dt
    except Exception:
        return None
    return None

def extract_timestamp_ocr(path: Path) -> Optional[datetime]:
    """
    OCR the timestamp from the TOP-LEFT overlay.
    Requires pytesseract + Tesseract installed on your machine.
    """
    try:
        import pytesseract  # type: ignore
    except Exception:
        return None

    try:
        img = Image.open(path).convert("RGB")
    except Exception:
        return None

    w, h = img.size
    crop = img.crop((0, 0, int(w * 0.38), int(h * 0.16)))
    gray = ImageOps.grayscale(crop)
    gray = ImageEnhance.Contrast(gray).enhance(2.5)
    gray = ImageEnhance.Sharpness(gray).enhance(2.0)
    bw = gray.point(lambda p: 255 if p > 155 else 0)

    try:
        text = pytesseract.image_to_string(bw, config="--psm 6")
    except Exception:
        return None

    dt = _parse_timestamp_str(text)
    if dt:
        return dt

    cleaned = re.sub(r'[^0-9:/\s]', ' ', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return _parse_timestamp_str(cleaned)

@dataclass
class PhotoItem:
    path: Path
    timestamp: datetime

def collect_photos(site_dir: Path, strict: bool) -> List[PhotoItem]:
    items: List[PhotoItem] = []
    for p in sorted(site_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in SUPPORTED_EXTS:
            continue

        try:
            img = Image.open(p)
        except Exception:
            if strict:
                raise RuntimeError(f"Cannot open image: {p}")
            else:
                continue

        dt = extract_timestamp_exif(img)
        if dt is None:
            dt = extract_timestamp_ocr(p)

        if dt is None:
            msg = f"Timestamp not found (EXIF/OCR): {p}"
            if strict:
                raise RuntimeError(msg + "\nTip: install Tesseract + pytesseract, or ensure EXIF DateTimeOriginal exists.")
            else:
                continue

        items.append(PhotoItem(path=p, timestamp=dt))

    items.sort(key=lambda x: (x.timestamp, x.path.name.lower()))
    return items

def draw_photo_page(c: canvas.Canvas, img_path: Path, ts_str: str) -> None:
    """
    One photo per page. Timestamp is OVERLAID on the photo (top-left).
    """
    with Image.open(img_path) as im:
        im = im.convert("RGB")
        w, h = im.size

        if w >= h:
            page_w, page_h = landscape(A4)
        else:
            page_w, page_h = portrait(A4)

        c.setPageSize((page_w, page_h))

        margin = 10 * mm
        box_w = page_w - 2 * margin
        box_h = page_h - 2 * margin

        scale = min(box_w / w, box_h / h)
        draw_w = w * scale
        draw_h = h * scale

        x = (page_w - draw_w) / 2
        y = (page_h - draw_h) / 2

        c.drawImage(str(img_path), x, y, width=draw_w, height=draw_h, preserveAspectRatio=True, mask='auto')

        # Timestamp overlay (top-left inside image)
        inset_x = 6 * mm
        inset_y = 6 * mm
        tx = x + inset_x
        ty_top = y + draw_h - inset_y

        font_name = "Helvetica"
        font_size = 10
        c.setFont(font_name, font_size)
        text_w = c.stringWidth(ts_str, font_name, font_size)

        pad_x = 2.0 * mm
        pad_y = 1.5 * mm
        rect_h = 6.0 * mm
        rect_w = text_w + 2 * pad_x

        # background box for readability
        c.saveState()
        c.setFillColorRGB(0, 0, 0)
        c.rect(tx - pad_x, ty_top - rect_h, rect_w, rect_h, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        # baseline inside the rectangle
        c.drawString(tx, ty_top - rect_h + 1.6 * mm, ts_str)
        c.restoreState()

        c.showPage()

def make_pdf(site_name: str, month_label: str, photos: List[PhotoItem], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{site_name} - {month_label}.pdf"

    c = canvas.Canvas(str(out_path))
    for item in photos:
        draw_photo_page(c, item.path, _format_timestamp(item.timestamp))
    c.save()
    return out_path

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Input month folder (contains site folders)")
    ap.add_argument("--month", required=True, help='Month label for filenames, e.g. "Jan 2026"')
    ap.add_argument("--output", default="Output", help="Output folder for PDFs")
    ap.add_argument("--strict", action="store_true", help="Fail if any photo lacks timestamp (recommended)")
    args = ap.parse_args()

    in_root = Path(args.input)
    out_root = Path(args.output)

    if not in_root.exists():
        raise SystemExit(f"Input folder not found: {in_root}")

    site_dirs = [p for p in sorted(in_root.iterdir()) if p.is_dir()]
    if not site_dirs:
        raise SystemExit(f"No site folders found under: {in_root}")

    print(f"Input:  {in_root}")
    print(f"Month:  {args.month}")
    print(f"Output: {out_root.resolve()}\n")

    made = []
    for site_dir in site_dirs:
        site_name = site_dir.name
        print(f"Processing site: {site_name}")
        photos = collect_photos(site_dir, strict=args.strict)
        if not photos:
            if args.strict:
                raise SystemExit(f"No valid photos found for site: {site_name}")
            else:
                print("  (skipped - no valid photos)")
                continue

        out_pdf = make_pdf(site_name, args.month, photos, out_root)
        made.append(out_pdf)
        print(f"  -> {out_pdf}")

    print("\nDone. PDFs created:")
    for p in made:
        print(f" - {p}")

if __name__ == "__main__":
    main()
