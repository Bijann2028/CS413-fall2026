"""Optional slide tooling; uses local Chromium through Playwright, offline.

From assigns/06/: python -B MySolution/presentation/build_pdf.py
Playwright is a build-time dependency only; tests and demos do not need it.
"""

import argparse
import json
import os
from pathlib import Path
import re
import shutil


def find_browser():
    candidates = [
        Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"))
        / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("PROGRAMFILES", "C:/Program Files"))
        / "Google/Chrome/Application/chrome.exe",
    ]
    for name in ("chromium", "chromium-browser", "google-chrome", "msedge"):
        executable = shutil.which(name)
        if executable:
            candidates.append(Path(executable))
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", type=Path, default=find_browser())
    parser.add_argument("--preview-dir", type=Path,
                        help="Optional screenshot directory outside the submission")
    args = parser.parse_args()
    if args.browser is None:
        parser.error("provide --browser PATH to a local Chromium, Chrome, or Edge executable")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        parser.error("PDF rebuilding requires the optional playwright package")

    root = Path(__file__).resolve().parent
    output = root.parent / "PRESENTATION.pdf"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=str(args.browser), headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1)
        page.goto((root / "slides.html").as_uri(), wait_until="load")
        page.emulate_media(media="print")
        audit = page.locator(".slide").evaluate_all("""slides => slides.map((slide, i) => {
            const box = slide.getBoundingClientRect();
            const overflow = [...slide.querySelectorAll('h1,h2,h3,p,li,pre,table,.flow,.card')]
                .filter(element => { const r = element.getBoundingClientRect();
                    return r.bottom > box.bottom - 65 || r.right > box.right - 25
                        || element.scrollWidth > element.clientWidth + 2; })
                .map(element => element.textContent.trim().slice(0, 100));
            return {slide: i + 1, title: slide.querySelector('h1,h2').textContent,
                    width: box.width, height: box.height, overflow};
        })""")
        if any(slide["overflow"] for slide in audit):
            raise SystemExit("Slide content overflows:\n" + json.dumps(audit, indent=2))
        page.pdf(path=str(output), print_background=True, prefer_css_page_size=True,
                 display_header_footer=False, tagged=True)
        if args.preview_dir:
            args.preview_dir.mkdir(parents=True, exist_ok=True)
            for index, slide in enumerate(page.locator(".slide").all(), 1):
                slide.screenshot(path=str(args.preview_dir / f"slide-{index:02d}.png"))
        browser.close()

    data = output.read_bytes()
    pages = len(re.findall(rb"/Type\s*/Page\b", data))
    if not data.startswith(b"%PDF-") or pages != len(audit):
        raise SystemExit(f"Unexpected PDF structure: {pages} pages for {len(audit)} slides")
    print(json.dumps({"pdf": str(output), "pages": pages, "bytes": len(data),
                      "overflow": False, "slides": audit}, indent=2))


if __name__ == "__main__":
    main()
