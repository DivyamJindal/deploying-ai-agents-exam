# SupportEscalator deck

Self-contained presentation. No build step, no dependencies installed locally —
all libraries (reveal.js, three.js, 3d-force-graph, fonts) load from CDN at
runtime.

## Run

```bash
# from the repo root
python -m http.server 8765 -d deck
# then open http://localhost:8765
```

Or just double-click `deck/index.html` (most browsers will block CDN scripts
from `file://` for some libraries — the http.server route is more reliable).

## Keyboard

- `→` / `←` — next / previous slide
- `S` — speaker notes
- `?` — full keyboard help
- `F` — fullscreen
- `Esc` — slide overview

## Aesthetic

Inspired by [supermemory.ai](https://supermemory.ai):

- Deep navy background (`#060a1a`) + subtle grid
- Electric blue + cyan accents (`#4f7dff`, `#00e0ff`)
- IBM Plex Sans (body) + JetBrains Mono (labels, code)
- Animated wireframe orb on the title slide (three.js)
- Interactive 3D force graph of the LangGraph architecture (3d-force-graph)
- Stat panels with mono labels, KPI cards with subtle radial gradients

## Slides

1. Title (orb)
2. Problem — Mosaic Cloud KPIs
3. Why LangGraph (vs single chatbot)
4. Architecture (live 3D graph)
5. Pydantic state schema + normalization layer
6. Demo path 1 — auto-resolution
7. Demo path 2 — refund escalation (interrupt + persistent resume)
8. Demo path 3 — sentiment escalation
9. KPIs & business impact
10. Edge cases
11. Learnings & next steps
12. Q&A / thank you

## Export to PDF

Open in Chrome / Chromium with `?print-pdf` appended:

```
http://localhost:8765/?print-pdf
```

Then `File → Print → Save as PDF`. Reveal.js handles pagination automatically.
