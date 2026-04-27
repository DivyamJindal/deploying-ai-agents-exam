"""Streamlit ticketing console for the SupportEscalator LangGraph agent."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st
from langgraph.types import Command

from support_escalator.data import load_accounts
from support_escalator.graph import build_graph
from support_escalator.models import SupportState, TicketInput
from support_escalator.ui_state import (
    extract_interrupt,
    get_field,
    summarize_run,
    to_plain,
)

ROOT = Path(__file__).parent
DEMO_TICKETS = json.loads((ROOT / "data" / "demo_tickets.json").read_text())
GRAPH_SVG_PATH = ROOT / "assets" / "support_escalator_graph.svg"
GRAPH_MMD_PATH = ROOT / "assets" / "support_escalator_graph.mmd"


# ---------------------------------------------------------------------------
# Page setup + theme
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="SupportEscalator Console",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="expanded",
)

THEME_CSS = """
<style>
:root {
  --bg: #0b1220;
  --bg-elev: #111a2e;
  --card: #15203a;
  --card-2: #1a2747;
  --border: rgba(148, 163, 184, 0.18);
  --text: #e2e8f0;
  --muted: #94a3b8;
  --accent: #38bdf8;
  --accent-2: #22d3ee;
  --ok: #34d399;
  --warn: #fbbf24;
  --danger: #f87171;
  --violet: #a78bfa;
}

html, body, [class*="css"] {
  font-family: 'Inter', 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
  background: radial-gradient(1200px 600px at 10% -10%, #142046 0%, transparent 60%),
              radial-gradient(900px 500px at 110% 10%, #0d2236 0%, transparent 55%),
              linear-gradient(180deg, #07101f 0%, #0b1220 100%);
  color: var(--text);
}

section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0a1326 0%, #0b1220 100%);
  border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] * { color: var(--text); }

.app-shell-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(56,189,248,0.10), rgba(167,139,250,0.08));
  margin-bottom: 16px;
}
.app-shell-header .brand { font-size: 18px; font-weight: 700; letter-spacing: 0.2px; }
.app-shell-header .brand .dot { color: var(--accent); margin-right: 8px; }
.app-shell-header .meta { color: var(--muted); font-size: 12px; }

.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px 18px;
  box-shadow: 0 1px 0 rgba(255,255,255,0.02) inset, 0 12px 30px rgba(2,6,23,0.35);
  margin-bottom: 14px;
}
.card h4 {
  margin: 0 0 8px 0; font-size: 13px; text-transform: uppercase;
  letter-spacing: 0.12em; color: var(--muted); font-weight: 600;
}
.card .body { color: var(--text); font-size: 14px; line-height: 1.55; }
.card .row { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 6px; }
.card .row span:first-child { color: var(--muted); font-size: 12px; }
.card .row span:last-child { color: var(--text); font-weight: 600; font-size: 13px; }

.kpi {
  background: linear-gradient(135deg, rgba(56,189,248,0.10), rgba(34,211,238,0.05));
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 14px 16px;
}
.kpi .label { color: var(--muted); font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; }
.kpi .value { font-size: 26px; font-weight: 700; margin-top: 4px; }
.kpi .sub { color: var(--muted); font-size: 12px; margin-top: 2px; }
.kpi.ok .value { color: var(--ok); }
.kpi.warn .value { color: var(--warn); }
.kpi.danger .value { color: var(--danger); }
.kpi.accent .value { color: var(--accent-2); }

.badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 3px 10px; border-radius: 999px;
  font-size: 11px; font-weight: 600; letter-spacing: 0.04em;
  border: 1px solid var(--border); background: rgba(148,163,184,0.08);
  color: var(--muted);
}
.badge.bug { color: var(--violet); border-color: rgba(167,139,250,0.45); background: rgba(167,139,250,0.10); }
.badge.billing { color: var(--accent-2); border-color: rgba(34,211,238,0.45); background: rgba(34,211,238,0.10); }
.badge.feature { color: #f0abfc; border-color: rgba(240,171,252,0.45); background: rgba(240,171,252,0.10); }
.badge.general { color: var(--accent); border-color: rgba(56,189,248,0.45); background: rgba(56,189,248,0.10); }
.badge.ok { color: var(--ok); border-color: rgba(52,211,153,0.45); background: rgba(52,211,153,0.10); }
.badge.warn { color: var(--warn); border-color: rgba(251,191,36,0.45); background: rgba(251,191,36,0.10); }
.badge.danger { color: var(--danger); border-color: rgba(248,113,113,0.45); background: rgba(248,113,113,0.10); }

.timeline { position: relative; padding-left: 18px; }
.timeline::before {
  content: ""; position: absolute; left: 6px; top: 6px; bottom: 6px;
  width: 2px; background: linear-gradient(180deg, var(--accent), var(--violet));
  opacity: 0.45; border-radius: 2px;
}
.timeline .step { position: relative; margin-bottom: 14px; padding-left: 12px; }
.timeline .step::before {
  content: ""; position: absolute; left: -16px; top: 6px;
  width: 12px; height: 12px; border-radius: 50%;
  background: var(--accent); box-shadow: 0 0 0 3px rgba(56,189,248,0.25);
}
.timeline .step.warn::before { background: var(--warn); box-shadow: 0 0 0 3px rgba(251,191,36,0.25); }
.timeline .step.danger::before { background: var(--danger); box-shadow: 0 0 0 3px rgba(248,113,113,0.25); }
.timeline .step.ok::before { background: var(--ok); box-shadow: 0 0 0 3px rgba(52,211,153,0.25); }
.timeline .step .title { font-weight: 600; font-size: 13px; }
.timeline .step .meta { color: var(--muted); font-size: 12px; margin-top: 2px; }

.queue-item {
  border: 1px solid var(--border); border-radius: 12px;
  padding: 10px 12px; margin-bottom: 8px; background: rgba(15,23,42,0.6);
}
.queue-item .t { font-weight: 600; font-size: 13px; }
.queue-item .s { color: var(--muted); font-size: 11px; margin-top: 4px; }

.response-card {
  white-space: pre-wrap;
  background: linear-gradient(135deg, rgba(52,211,153,0.08), rgba(56,189,248,0.06));
  border: 1px solid rgba(52,211,153,0.25);
  border-radius: 12px;
  padding: 14px 16px; color: var(--text); font-size: 14px; line-height: 1.6;
}

.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] {
  background: rgba(15,23,42,0.5);
  border: 1px solid var(--border);
  border-bottom: none;
  border-radius: 10px 10px 0 0;
  padding: 8px 14px;
  color: var(--muted);
}
.stTabs [aria-selected="true"] {
  background: var(--card-2) !important; color: var(--text) !important;
  border-color: rgba(56,189,248,0.45) !important;
}

div.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  border: 0; color: #06121f; font-weight: 700;
}
div.stButton > button { border-radius: 10px; }

[data-testid="stMetricValue"] { color: var(--text); }
[data-testid="stMetricLabel"] { color: var(--muted) !important; }
</style>
"""

st.markdown(THEME_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"ticket-{uuid4().hex[:8]}"
if "graph" not in st.session_state:
    st.session_state.graph = build_graph()
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "pending_interrupt" not in st.session_state:
    st.session_state.pending_interrupt = None
if "history" not in st.session_state:
    st.session_state.history = []  # list of summarize_run() dicts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CATEGORY_BADGE = {"bug": "bug", "billing": "billing", "feature": "feature", "general": "general"}


def config():
    return {"configurable": {"thread_id": st.session_state.thread_id}}


def capture_result(result) -> None:
    plain = to_plain(result)
    st.session_state.last_result = plain
    st.session_state.pending_interrupt = extract_interrupt(result)
    if not st.session_state.pending_interrupt and plain.get("final_response"):
        summary = summarize_run(plain)
        summary["thread_id"] = st.session_state.thread_id
        summary["completed_at"] = datetime.utcnow().isoformat(timespec="seconds")
        st.session_state.history.append(summary)


def reset_thread() -> None:
    st.session_state.thread_id = f"ticket-{uuid4().hex[:8]}"
    st.session_state.graph = build_graph()
    st.session_state.last_result = None
    st.session_state.pending_interrupt = None


def category_badge_html(category: str | None) -> str:
    if not category:
        return '<span class="badge">unclassified</span>'
    cls = CATEGORY_BADGE.get(category, "general")
    return f'<span class="badge {cls}">{category.upper()}</span>'


def status_badge_html(state: dict) -> str:
    if st.session_state.pending_interrupt:
        return '<span class="badge danger">⚠ Awaiting Supervisor</span>'
    if state and state.get("final_response"):
        return '<span class="badge ok">✓ Resolved</span>'
    return '<span class="badge">Idle</span>'


def sentiment_badge_html(score: float) -> str:
    if score >= 0.67:
        return f'<span class="badge danger">Sentiment {score:.2f} — frustrated</span>'
    if score >= 0.34:
        return f'<span class="badge warn">Sentiment {score:.2f} — tense</span>'
    return f'<span class="badge ok">Sentiment {score:.2f} — calm</span>'


def render_kpi(label: str, value: str, sub: str = "", tone: str = "") -> str:
    tone_cls = f" {tone}" if tone else ""
    return (
        f'<div class="kpi{tone_cls}"><div class="label">{label}</div>'
        f'<div class="value">{value}</div>'
        f'<div class="sub">{sub}</div></div>'
    )


def render_account_card(account_id: str) -> None:
    accounts = load_accounts()
    account = accounts.get(account_id)
    if not account:
        st.markdown(
            f'<div class="card"><h4>Account</h4>'
            f'<div class="body">No account record for <code>{account_id}</code>.</div></div>',
            unsafe_allow_html=True,
        )
        return
    risk = "danger" if account.eligible_refund > 200 else ("warn" if account.eligible_refund > 0 else "ok")
    st.markdown(
        f"""
<div class="card">
  <h4>Customer & Account</h4>
  <div class="row"><span>Account</span><span>{account.customer_name} ({account.account_id})</span></div>
  <div class="row"><span>Plan</span><span>{account.plan}</span></div>
  <div class="row"><span>MRR</span><span>${account.mrr:,.0f}</span></div>
  <div class="row"><span>Last invoice</span><span>${account.last_invoice_amount:,.0f}</span></div>
  <div class="row"><span>Duplicate charge</span><span>{'Yes' if account.duplicate_charge else 'No'}</span></div>
  <div class="row"><span>Refund exposure</span>
    <span><span class="badge {risk}">${account.eligible_refund:,.0f}</span></span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_timeline(state: dict) -> None:
    pending = st.session_state.pending_interrupt
    steps: list[tuple[str, str, str]] = []  # (tone, title, meta)

    category = state.get("category")
    if category:
        steps.append(("ok", "Classifier", f"routed → {category}_solver"))
    else:
        steps.append(("", "Classifier", "pending"))

    score = float(state.get("sentiment_score") or 0.0)
    if score >= 0.67:
        tone = "danger"
    elif score >= 0.34:
        tone = "warn"
    else:
        tone = "ok"
    steps.append((tone, "Sentiment Monitor", f"score = {score:.2f}"))

    attempts = state.get("resolution_attempts") or []
    for attempt in attempts:
        node = get_field(attempt, "node", "solver")
        resolved = bool(get_field(attempt, "resolved", False))
        summary = get_field(attempt, "summary", "")
        tone = "ok" if resolved else "warn"
        meta = f"{'resolved' if resolved else 'needs follow-up'} — {summary[:120]}"
        steps.append((tone, node, meta))

    if pending:
        reason = pending.get("escalation_reason", "supervisor review needed")
        steps.append(("danger", "Escalation Gate", f"interrupt → {reason}"))
    elif state.get("escalation_reason"):
        steps.append(("warn", "Escalation Gate", f"resolved after escalation: {state['escalation_reason']}"))
    else:
        steps.append(("ok", "Escalation Gate", "no escalation needed"))

    if state.get("final_response"):
        steps.append(("ok", "Response Composer", "final reply ready"))
    elif pending:
        steps.append(("", "Response Composer", "waiting on supervisor"))

    rows = "".join(
        f'<div class="step {tone}"><div class="title">{title}</div>'
        f'<div class="meta">{meta}</div></div>'
        for tone, title, meta in steps
    )
    st.markdown(
        f'<div class="card"><h4>Resolution Timeline</h4><div class="timeline">{rows}</div></div>',
        unsafe_allow_html=True,
    )


def render_attempts(state: dict) -> None:
    attempts = state.get("resolution_attempts") or []
    if not attempts:
        st.info("No solver output yet.")
        return
    for attempt in attempts:
        node = get_field(attempt, "node", "solver")
        resolved = bool(get_field(attempt, "resolved", False))
        summary = get_field(attempt, "summary", "")
        evidence = get_field(attempt, "evidence", []) or []
        chip = '<span class="badge ok">resolved</span>' if resolved else '<span class="badge warn">needs follow-up</span>'
        evidence_html = ""
        if evidence:
            evidence_html = (
                '<div class="row"><span>Evidence</span>'
                f'<span>{", ".join(str(e) for e in evidence)}</span></div>'
            )
        st.markdown(
            f"""
<div class="card">
  <h4>{node} {chip}</h4>
  <div class="body">{summary}</div>
  {evidence_html}
</div>
""",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### 🎟️ SupportEscalator")
    st.caption("Ops console · LangGraph multi-agent")

    st.divider()
    st.markdown("**Active thread**")
    st.code(st.session_state.thread_id, language="text")
    if st.button("➕ New ticket thread", use_container_width=True):
        reset_thread()
        st.rerun()

    st.divider()
    st.markdown("**Demo queue**")
    preset_titles = [t["title"] for t in DEMO_TICKETS]
    preset_title = st.radio(
        "Choose a ticket",
        preset_titles,
        index=0,
        label_visibility="collapsed",
    )
    preset = next(t for t in DEMO_TICKETS if t["title"] == preset_title)
    for t in DEMO_TICKETS:
        active = "border-color: rgba(56,189,248,0.55);" if t["title"] == preset_title else ""
        st.markdown(
            f'<div class="queue-item" style="{active}">'
            f'<div class="t">{t["title"]}</div>'
            f'<div class="s">{t["account_id"]} · {t["customer_email"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("**Session stats**")
    h = st.session_state.history
    st.metric("Tickets resolved", len(h))
    if h:
        escalated = sum(1 for r in h if r.get("escalation_reason"))
        st.metric("Escalation rate", f"{escalated/len(h)*100:.0f}%")


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

state = st.session_state.last_result or {}
header_status = status_badge_html(state)
header_category = category_badge_html(state.get("category")) if state else ""

st.markdown(
    f"""
<div class="app-shell-header">
  <div>
    <div class="brand"><span class="dot">●</span>SupportEscalator Console</div>
    <div class="meta">LangGraph routing · Sentiment-aware · Human-in-the-loop escalation</div>
  </div>
  <div>{header_category} {header_status}</div>
</div>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

inbox_tab, supervisor_tab, analytics_tab, architecture_tab = st.tabs(
    ["📥 Inbox", "🛡 Supervisor", "📊 Analytics", "🧭 Architecture"]
)


# -- Inbox -----------------------------------------------------------------

with inbox_tab:
    left, right = st.columns([1.05, 1])
    with left:
        st.markdown('<div class="card"><h4>Ticket Intake</h4></div>', unsafe_allow_html=True)
        with st.form("ticket_form", clear_on_submit=False):
            title = st.text_input("Title", value=preset["title"])
            account_id = st.text_input("Account ID", value=preset["account_id"])
            customer_email = st.text_input("Customer email", value=preset["customer_email"])
            message = st.text_area("Message", value=preset["message"], height=160)
            submitted = st.form_submit_button("Run SupportEscalator", type="primary", use_container_width=True)
        if submitted:
            ticket = TicketInput(
                title=title,
                account_id=account_id,
                customer_email=customer_email,
                message=message,
            )
            initial_state = SupportState(ticket=ticket)
            with st.spinner("Running graph: classifier → sentiment → solver → escalation gate"):
                result = st.session_state.graph.invoke(initial_state, config=config())
            capture_result(result)
            st.rerun()

    with right:
        if state:
            score = float(state.get("sentiment_score") or 0.0)
            st.markdown(
                f"""
<div class="card">
  <h4>Ticket Snapshot</h4>
  <div class="row"><span>Title</span><span>{(state.get("ticket") or {}).get("title", "—")}</span></div>
  <div class="row"><span>Requester</span><span>{(state.get("ticket") or {}).get("customer_email", "—")}</span></div>
  <div class="row"><span>Category</span><span>{category_badge_html(state.get("category"))}</span></div>
  <div class="row"><span>Sentiment</span><span>{sentiment_badge_html(score)}</span></div>
  <div class="row"><span>Status</span><span>{status_badge_html(state)}</span></div>
</div>
""",
                unsafe_allow_html=True,
            )
            render_account_card((state.get("ticket") or {}).get("account_id", account_id))
        else:
            st.markdown(
                '<div class="card"><h4>Ticket Snapshot</h4>'
                '<div class="body">Submit a ticket on the left to see it routed through the graph. '
                'Try the three demo tickets in the sidebar to exercise autonomous resolution, '
                'a billing refund interrupt, and a sentiment-driven escalation.</div></div>',
                unsafe_allow_html=True,
            )

    st.divider()
    if state:
        render_timeline(state)

        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.markdown('<div class="card"><h4>Solver Attempts</h4></div>', unsafe_allow_html=True)
            render_attempts(state)
        with col_b:
            if st.session_state.pending_interrupt:
                pending = st.session_state.pending_interrupt
                st.markdown(
                    f"""
<div class="card" style="border-color: rgba(248,113,113,0.4);">
  <h4>⚠ Awaiting Supervisor Decision</h4>
  <div class="body">
    <strong>Reason:</strong> {pending.get("escalation_reason", "")}<br/>
    <strong>Auto-resolution attempt:</strong> {pending.get("auto_resolution", "")}
  </div>
</div>
""",
                    unsafe_allow_html=True,
                )
                st.info("Open the **Supervisor** tab to approve or reject the escalation.")
            elif state.get("final_response"):
                st.markdown('<div class="card"><h4>Final Customer Response</h4></div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="response-card">{state["final_response"]}</div>',
                    unsafe_allow_html=True,
                )
                st.download_button(
                    "Copy response as .txt",
                    data=state["final_response"],
                    file_name=f"{st.session_state.thread_id}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )


# -- Supervisor -----------------------------------------------------------

with supervisor_tab:
    pending = st.session_state.pending_interrupt
    if not pending:
        st.markdown(
            '<div class="card"><h4>Supervisor Workspace</h4>'
            '<div class="body">No tickets are paused right now. Run the duplicate billing or '
            'angry upload demo ticket to trigger an interrupt at the escalation gate.</div></div>',
            unsafe_allow_html=True,
        )
    else:
        ticket = pending.get("ticket", {})
        score = float(pending.get("sentiment_score") or 0.0)
        st.markdown(
            f"""
<div class="card" style="border-color: rgba(248,113,113,0.45);">
  <h4>⚠ Escalation Gate Interrupt</h4>
  <div class="body"><strong>Reason:</strong> {pending.get("escalation_reason","")}</div>
</div>
""",
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.markdown(
                f"""
<div class="card">
  <h4>Ticket</h4>
  <div class="row"><span>Title</span><span>{ticket.get("title","—")}</span></div>
  <div class="row"><span>Account</span><span>{ticket.get("account_id","—")}</span></div>
  <div class="row"><span>Requester</span><span>{ticket.get("customer_email","—")}</span></div>
  <div class="row"><span>Category</span><span>{category_badge_html(pending.get("category"))}</span></div>
  <div class="row"><span>Sentiment</span><span>{sentiment_badge_html(score)}</span></div>
</div>
""",
                unsafe_allow_html=True,
            )
            render_account_card(ticket.get("account_id", ""))

        with col_b:
            st.markdown(
                f"""
<div class="card">
  <h4>Auto-resolution Attempt</h4>
  <div class="body">{pending.get("auto_resolution","")}</div>
</div>
""",
                unsafe_allow_html=True,
            )
            with st.form("supervisor_form"):
                approved = st.radio("Decision", ["approve", "reject"], horizontal=True)
                guidance = st.text_area(
                    "Supervisor guidance",
                    value="Apologise, keep the case open, and route the incident details to the right owner with a same-day follow-up.",
                    height=140,
                )
                responder_name = st.text_input("Supervisor name", value="Supervisor A")
                resume = st.form_submit_button("Resume graph", type="primary", use_container_width=True)
            if resume:
                decision = {
                    "approved": approved == "approve",
                    "guidance": guidance,
                    "responder_name": responder_name,
                }
                with st.spinner("Resuming graph with supervisor decision…"):
                    result = st.session_state.graph.invoke(Command(resume=decision), config=config())
                capture_result(result)
                st.rerun()

        st.markdown(
            f"""
<div class="card">
  <h4>Raw Interrupt Payload</h4>
  <div class="body"><pre style="white-space: pre-wrap; color: var(--muted); font-size: 12px;">{json.dumps(pending, indent=2)}</pre></div>
</div>
""",
            unsafe_allow_html=True,
        )


# -- Analytics ------------------------------------------------------------

with analytics_tab:
    history = st.session_state.history
    total = len(history)
    escalated = sum(1 for r in history if r.get("escalation_reason"))
    auto_rate = ((total - escalated) / total * 100) if total else 0.0
    avg_sent = (sum(r.get("sentiment_score", 0.0) for r in history) / total) if total else 0.0
    refund_exposure = sum(
        load_accounts().get(r.get("account_id", ""), None).eligible_refund
        if load_accounts().get(r.get("account_id", "")) else 0
        for r in history
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        render_kpi("Tickets handled", str(total), "since session start", "accent"),
        unsafe_allow_html=True,
    )
    c2.markdown(
        render_kpi("Auto-resolution", f"{auto_rate:.0f}%", f"{total - escalated}/{total or 1} no-escalation", "ok"),
        unsafe_allow_html=True,
    )
    c3.markdown(
        render_kpi("Escalations", str(escalated), f"of {total or 1} tickets", "warn" if escalated else ""),
        unsafe_allow_html=True,
    )
    c4.markdown(
        render_kpi("Avg sentiment score", f"{avg_sent:.2f}", "0 = calm · 1 = furious",
                   "danger" if avg_sent >= 0.67 else ("warn" if avg_sent >= 0.34 else "ok")),
        unsafe_allow_html=True,
    )

    st.divider()

    if not history:
        st.markdown(
            '<div class="card"><h4>Analytics</h4>'
            '<div class="body">Run a few demo tickets to populate KPIs and charts. '
            'The session tracks category mix, sentiment, and escalation reasons live.</div></div>',
            unsafe_allow_html=True,
        )
    else:
        df = pd.DataFrame(history)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="card"><h4>Ticket Category Mix</h4></div>', unsafe_allow_html=True)
            cat_counts = (
                df["category"].fillna("unclassified").value_counts().rename_axis("category").reset_index(name="tickets")
            )
            st.bar_chart(cat_counts.set_index("category"), height=240)

        with col_b:
            st.markdown('<div class="card"><h4>Solver Outcome</h4></div>', unsafe_allow_html=True)
            outcome = df.assign(
                outcome=df["solver_resolved"].map({True: "auto-resolved", False: "needs follow-up"})
            )
            outcome_counts = (
                outcome.groupby(["solver", "outcome"]).size().reset_index(name="tickets")
                .pivot(index="solver", columns="outcome", values="tickets").fillna(0)
            )
            st.bar_chart(outcome_counts, height=240)

        col_c, col_d = st.columns(2)
        with col_c:
            st.markdown('<div class="card"><h4>Sentiment Across Tickets</h4></div>', unsafe_allow_html=True)
            st.line_chart(
                df[["ticket_title", "sentiment_score"]].set_index("ticket_title"),
                height=240,
            )
        with col_d:
            st.markdown('<div class="card"><h4>Escalation Reasons</h4></div>', unsafe_allow_html=True)
            reasons = (
                df["escalation_reason"].dropna().str.split(";").explode().str.strip()
                .replace("", pd.NA).dropna()
            )
            if reasons.empty:
                st.info("No escalations yet.")
            else:
                reason_counts = reasons.value_counts().rename_axis("reason").reset_index(name="count")
                st.bar_chart(reason_counts.set_index("reason"), height=240)

        st.markdown('<div class="card"><h4>Recent Tickets</h4></div>', unsafe_allow_html=True)
        st.dataframe(
            df[
                [
                    "completed_at",
                    "ticket_title",
                    "account_id",
                    "category",
                    "sentiment_score",
                    "solver",
                    "solver_resolved",
                    "escalation_reason",
                ]
            ].iloc[::-1].reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )


# -- Architecture ---------------------------------------------------------

with architecture_tab:
    col_a, col_b = st.columns([1.4, 1])
    with col_a:
        st.markdown('<div class="card"><h4>Agent Architecture</h4></div>', unsafe_allow_html=True)
        if GRAPH_SVG_PATH.exists():
            st.image(str(GRAPH_SVG_PATH), use_container_width=True)
        else:
            st.info("Run `python scripts/draw_graph.py` to generate the architecture SVG.")
        if GRAPH_MMD_PATH.exists():
            with st.expander("Mermaid source"):
                st.code(GRAPH_MMD_PATH.read_text(), language="mermaid")
    with col_b:
        st.markdown(
            """
<div class="card">
  <h4>What This Demonstrates</h4>
  <div class="body">
    <ul>
      <li><b>Conditional routing</b> — classifier dispatches to bug, billing, feature, or general solvers.</li>
      <li><b>Sentiment monitor</b> — frustration scoring feeds the escalation gate.</li>
      <li><b>Human-in-the-loop</b> — <code>escalation_gate</code> pauses with <code>interrupt()</code>.</li>
      <li><b>Resume</b> — supervisor decision is injected via <code>Command(resume=…)</code>.</li>
      <li><b>Stateful</b> — Pydantic <code>SupportState</code> with <code>MemorySaver</code> checkpointing.</li>
    </ul>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown(
            """
<div class="card">
  <h4>Demo Flows</h4>
  <div class="body">
    <ol>
      <li><b>Password reset</b> → autonomous general resolution.</li>
      <li><b>Duplicate billing charge</b> → refund threshold interrupt.</li>
      <li><b>Angry upload bug</b> → sentiment + unresolved interrupt.</li>
    </ol>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    if state:
        with st.expander("Normalized graph state (JSON)", expanded=False):
            st.json(state)
