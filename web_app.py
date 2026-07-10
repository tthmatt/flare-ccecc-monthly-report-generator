#!/usr/bin/env python3
"""Browser-based GUI for the monthly photo report generator."""

from __future__ import annotations

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
import cgi
import html
import io
import tempfile
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from typing import Iterable
from urllib.parse import quote

from make_reports import collect_photos, make_pdf

HOST = "127.0.0.1"
PORT = 5000


_SAFE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._- "


def secure_filename(name: str) -> str:
    cleaned = "".join(ch if ch in _SAFE_CHARS else "_" for ch in name).strip(" ._")
    return cleaned.replace(" ", "_")


PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Flare Dynamics Monthly Photo Report Generator</title>
  <style>
    :root { color-scheme: light; font-family: Arial, Helvetica, sans-serif; --flare-red: #ed2024; --flare-charcoal: #222; --flare-gray: #5c5c5c; }
    body { margin: 0; background: linear-gradient(135deg, #f7f7f8 0%, #f4f7fb 55%, #fff1f1 100%); color: #1f2937; }
    .wrap { max-width: 920px; margin: 0 auto; padding: 36px 20px; }
    .brand { display: flex; align-items: center; gap: 18px; margin-bottom: 24px; }
    .brand-logo { width: min(360px, 70vw); height: auto; display: block; }
    .brand-name { margin: 0; color: var(--flare-gray); font-size: 14px; font-weight: 800; letter-spacing: .18em; text-transform: uppercase; }
    .card { background: white; border-top: 6px solid var(--flare-red); border-radius: 18px; box-shadow: 0 18px 45px rgba(31,41,55,.12); padding: 30px; }
    h1 { margin: 0 0 8px; font-size: 30px; color: var(--flare-charcoal); }
    .lead { margin: 0 0 26px; color: #4b5563; line-height: 1.5; }
    .steps { display: grid; gap: 12px; margin: 0 0 28px; padding: 0; list-style: none; }
    .steps li { background: #fff5f5; border-left: 5px solid var(--flare-red); border-radius: 10px; padding: 12px 14px; }
    label { display: block; font-weight: 700; margin: 18px 0 8px; }
    input[type="text"], input[type="file"] { width: 100%; box-sizing: border-box; padding: 12px; border: 1px solid #cbd5e1; border-radius: 10px; font-size: 16px; background: white; }
    .hint { color: #64748b; font-size: 14px; margin-top: 6px; line-height: 1.4; }
    .check { display: flex; gap: 10px; align-items: flex-start; margin: 18px 0; }
    .check input { margin-top: 3px; }
    button { background: var(--flare-red); color: white; border: 0; border-radius: 12px; padding: 14px 20px; font-size: 17px; font-weight: 700; cursor: pointer; }
    button:hover { background: #c91418; }
    .messages { border-radius: 10px; padding: 12px 14px; margin-bottom: 20px; background: #fee2e2; color: #991b1b; }
    .footer { text-align: center; color: #64748b; font-size: 13px; margin-top: 18px; }
  </style>
</head>
<body>
  <main class="wrap">
    <section class="card">
      <header class="brand" aria-label="Flare Dynamics">
        <img class="brand-logo" src="/assets/flare-dynamics-logo.svg" alt="Flare Dynamics logo">
        <p class="brand-name">Flare Dynamics</p>
      </header>
      <h1>Flare Dynamics Monthly Photo Report Generator</h1>
      <p class="lead">Create the site PDF reports from your browser. Select the month folder that contains one folder per site, enter the month label, then download a ZIP containing the generated PDFs.</p>
      {message}
      <ul class="steps">
        <li><strong>1.</strong> Put photos in folders like <code>Jan 2026 / TPE Tampines / photos...</code>.</li>
        <li><strong>2.</strong> Choose that month folder below.</li>
        <li><strong>3.</strong> Click <strong>Generate PDF ZIP</strong> and save the download.</li>
      </ul>
      <form action="/generate" method="post" enctype="multipart/form-data">
        <label for="month">Month label for PDF filenames</label>
        <input id="month" name="month" type="text" value="Jan 2026" placeholder="Example: Jan 2026" required>
        <div class="hint">Output files will be named like <code>Site Name - Jan 2026.pdf</code>.</div>
        <label for="photos">Month folder</label>
        <input id="photos" name="photos" type="file" webkitdirectory directory multiple required>
        <div class="hint">Choose the folder that contains the site folders. Chrome, Edge, and Safari support folder selection.</div>
        <div class="check">
          <input id="strict" name="strict" type="checkbox" checked>
          <div>
            <label for="strict" style="display:inline; margin:0;">Strict mode</label>
            <div class="hint">Stops if a photo is missing a timestamp. Turn this off to skip photos without timestamps.</div>
          </div>
        </div>
        <button type="submit">Generate PDF ZIP</button>
      </form>
    </section>
    <p class="footer">This app runs locally on your computer; selected photos are processed by this local Python app.</p>
  </main>
</body>
</html>
"""


def _safe_parts(upload_name: str) -> list[str]:
    parts = [p for p in PurePosixPath(upload_name.replace("\\", "/")).parts if p not in ("", ".", "..")]
    return [secure_filename(part) or "unnamed" for part in parts]


def _as_list(value: object) -> list[object]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _save_uploads(fields: cgi.FieldStorage, input_root: Path) -> None:
    for uploaded in _as_list(fields["photos"] if "photos" in fields else None):
        if not getattr(uploaded, "filename", ""):
            continue
        parts = _safe_parts(uploaded.filename)
        if len(parts) < 2:
            continue
        destination = input_root.joinpath(*parts[1:])
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as out_file:
            while True:
                chunk = uploaded.file.read(1024 * 1024)
                if not chunk:
                    break
                out_file.write(chunk)


def _zip_pdfs(pdf_paths: Iterable[Path]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for pdf_path in pdf_paths:
            archive.write(pdf_path, arcname=pdf_path.name)
    return buffer.getvalue()


class ReportWebHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path.startswith("/assets/"):
            self._send_asset(self.path.removeprefix("/assets/"))
            return
        self._send_page()

    def do_POST(self) -> None:
        if self.path != "/generate":
            self.send_error(404)
            return
        try:
            fields = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": self.headers.get("Content-Type", ""),
                },
            )
            month_field = fields["month"] if "month" in fields else None
            month_label = getattr(month_field, "value", "").strip()
            strict = "strict" in fields
            if not month_label:
                self._send_page("Please enter a month label such as Jan 2026.")
                return
            if "photos" not in fields:
                self._send_page("Please choose a month folder containing site folders and photos.")
                return

            with tempfile.TemporaryDirectory(prefix="report-web-") as tmp:
                tmp_path = Path(tmp)
                input_root = tmp_path / "input"
                output_root = tmp_path / "output"
                input_root.mkdir()
                _save_uploads(fields, input_root)
                site_dirs = [p for p in sorted(input_root.iterdir()) if p.is_dir()]
                if not site_dirs:
                    self._send_page("No site folders were found. Choose the month folder that contains one folder per site.")
                    return
                made: list[Path] = []
                for site_dir in site_dirs:
                    photos = collect_photos(site_dir, strict=strict)
                    if photos:
                        made.append(make_pdf(site_dir.name, month_label, photos, output_root))
                    elif strict:
                        raise RuntimeError(f"No valid photos found for site: {site_dir.name}")
                if not made:
                    self._send_page("No PDFs were created. Check that the selected folder contains supported photo files.")
                    return
                zip_data = _zip_pdfs(made)
                download_name = f"monthly-photo-reports-{secure_filename(month_label) or 'reports'}.zip"
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{quote(download_name)}")
                self.send_header("Content-Length", str(len(zip_data)))
                self.end_headers()
                self.wfile.write(zip_data)
        except Exception as exc:
            self._send_page(str(exc))


    def _send_asset(self, asset_path: str) -> None:
        asset = Path(__file__).with_name("assets") / secure_filename(asset_path)
        if not asset.is_file():
            self.send_error(404)
            return
        data = asset.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_page(self, message: str = "") -> None:
        message_html = f'<div class="messages">{html.escape(message)}</div>' if message else ""
        body = PAGE.replace("{message}", message_html).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    url = f"http://{HOST}:{PORT}"
    print(f"Starting web GUI at {url}", flush=True)
    ThreadingHTTPServer((HOST, PORT), ReportWebHandler).serve_forever()


if __name__ == "__main__":
    main()
