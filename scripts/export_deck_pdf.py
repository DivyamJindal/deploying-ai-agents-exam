"""Export the Reveal.js deck to PDF for submission.

The deck must be served over HTTP (not file://) for Reveal.js to load its
print stylesheet from the CDN. Run a local static server in another shell:

    cd deck && python3 -m http.server 9876

Then run:

    python scripts/export_deck_pdf.py
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

DECK_URL = "http://localhost:9876/index.html?print-pdf"
OUTPUT = Path(__file__).resolve().parents[1] / "deck" / "SupportEscalator-Group_9.pdf"


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = ctx.new_page()
        page.goto(DECK_URL, wait_until="networkidle", timeout=60000)
        # Reveal.js needs a tick to lay out slide-by-slide for print-pdf.
        page.wait_for_timeout(4000)
        page.pdf(
            path=str(OUTPUT),
            width="1600px",
            height="1000px",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            prefer_css_page_size=False,
        )
        browser.close()
        print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
