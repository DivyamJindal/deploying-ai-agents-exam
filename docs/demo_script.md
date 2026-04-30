# SupportEscalator — 3-Minute Demo Script

> Hard cap: 3:00 total. Plays during the **Demo** segment of the live presentation
> (rubric requires pre-recorded video). Screen capture + voiceover only.

## Setup before recording

1. Reset state so the run-history sidebar starts clean:
   ```bash
   rm -f checkpoints/se.sqlite
   ```
2. Start the app:
   ```bash
   PYTHONPATH=src streamlit run app.py
   ```
3. Use a 1440×900 browser window. Hide bookmarks. Light/dark OS chrome
   does not matter — the app is dark.
4. OBS / QuickTime: 30 fps, microphone normalized to about -12 dB.

## Shot list (3:00, broken down)

### 0:00 – 0:15 · Title card + framing (15s)

**Voice:** "SupportEscalator is a LangGraph agent for SaaS support.
Routine tickets resolve themselves. Risky ones pause for a human
supervisor. The state survives restarts."

**Screen:** Streamlit header with the **Mode pill** (`LLM` if key set,
else `Rule-based`) and the empty inbox.

### 0:15 – 0:55 · Path 1 — Auto-resolution (40s)

**Voice:** "First ticket — a password reset. Classifier sends it to
`general_solver`, sentiment is calm, escalation gate passes through,
response composer ships the reply. End to end in about two seconds.
This 68 percent of tickets never sees a human."

**Screen:**
1. Sidebar → click **Password reset** demo ticket.
2. Click **Run**.
3. Camera dwells on the resolution timeline animating node-by-node.
4. Final response card pops, header shows green ✓ chip.
5. Cut to **Analytics** tab for one second — *Auto-resolution rate*
   KPI now reads `100 %` for this single ticket.

### 0:55 – 1:55 · Path 2 — Refund interrupt (60s)

**Voice:** "Second ticket — duplicate billing for invoice 42. Billing
solver finds the duplicate but the eligible refund is $499 — over our
$200 threshold. The escalation gate calls LangGraph's `interrupt()`
and the graph pauses. The state is saved to SQLite."

**Screen:**
1. Sidebar → **Duplicate billing charge** demo ticket → **Run**.
2. Header flips to amber: *Awaiting supervisor*.
3. Switch to **Supervisor** workspace.
4. Camera shows the escalation card: reason = refund > $200,
   sentiment = 0.10, account context with $499 refund exposure.

**Voice:** "Now the proof point. I kill Streamlit."

5. In the terminal: `Ctrl-C` to stop the server.
6. Restart immediately: `PYTHONPATH=src streamlit run app.py`.
7. Sidebar → **Resume previous thread** → pick the paused thread.
8. The supervisor card is back, exact same context.

**Voice:** "Same state, picked up at the exact node it paused on. I
approve with guidance."

9. Type guidance: `Refund approved — confirm via Stripe and apologise
   for the wait.` → **Approve & resume**.
10. Final response composes; supervisor guidance is folded in.

### 1:55 – 2:35 · Path 3 — Sentiment escalation (40s)

**Voice:** "Third ticket — angry customer, upload bug. Sentiment
fires at 0.80, the bug solver returns `resolved=False`. Two
independent risk signals — refund threshold doesn't trip here, but
tone does."

**Screen:**
1. Sidebar → **Angry upload bug** demo → **Run**.
2. Inbox header flips amber. Sentiment KPI spikes red.
3. Switch to **Supervisor** view.
4. Reject the auto-response, type guidance:
   `Engineering will respond in <2h. Keep ticket open.`
5. Cut to final response card — text shows the rejection guidance,
   ticket stays *open*, not auto-resolved.

### 2:35 – 3:00 · Architecture + tests (25s)

**Voice:** "The whole thing is one Pydantic state, eight nodes, one
interrupt, one SqliteSaver. Seventeen tests pass. Repo is public."

**Screen:**
1. Switch to **Architecture** tab.
2. Camera dwells on the SVG state diagram + the live normalized JSON.
3. Cut to terminal:
   ```bash
   PYTHONPATH=src pytest -q
   # 17 passed in 0.21s
   ```
4. Final card with the GitHub URL.

## Voiceover guard rails

- Do not say "I think" or "hopefully". State what the system does.
- Do not narrate node names that aren't on screen at the same moment.
- Numbers used in narration must match what the screen shows (refund
  $499, threshold $200, sentiment 0.80, tests 17).

## Export

- File: `demo.mp4`, H.264, 1080p, max 50MB.
- Upload to YouTube **unlisted** (or Drive with link sharing).
- Paste the URL into the README under "Demo video".
