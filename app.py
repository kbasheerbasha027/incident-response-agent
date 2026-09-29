import os
import json
import re
from html import escape
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from hindsight_client import Hindsight
from groq import Groq


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")
HINDSIGHT_BASE_URL = os.getenv(
    "HINDSIGHT_BASE_URL",
    "https://api.hindsight.vectorize.io"
)

HINDSIGHT_BANK_ID = "Incident Experience"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Recommended fast model
GROQ_MODEL = "openai/gpt-oss-120b"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Incident Response Agent",
    page_icon="IR",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
    :root {
        color-scheme: dark;
        --canvas: #11120f;
        --surface: #191a16;
        --surface-raised: #20211b;
        --paper: #e8e6db;
        --line: #34362e;
        --text: #efeee7;
        --muted: #a7a79a;
        --accent: #d5f36a;
        --accent-deep: #aaca43;
        --amber: #e4ad62;
        --red: #ee766d;
        --green: #a6bf7e;
    }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background: var(--canvas);
        color: var(--text);
    }
    [data-testid="stAppViewContainer"] {
        background-image: linear-gradient(118deg, rgba(213, 243, 106, .035), transparent 32%);
    }
    [data-testid="stSidebar"] {
        background: #151611;
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.25rem; }
    .block-container { max-width: 1460px; padding: 2rem 2.7rem 3.2rem; min-height: auto; overflow: visible; }
    h1, h2, h3 { color: var(--text); letter-spacing: 0; overflow-wrap: anywhere; }
    h1 { font-size: 2.45rem; font-weight: 650; line-height: 1.08; }
    h2 { font-size: 1.38rem; font-weight: 620; }
    h3 { font-size: 1.02rem; font-weight: 620; }
    p, label, [data-testid="stMarkdownContainer"] { color: #e1e0d6; }
    [data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"] p,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        overflow-wrap: anywhere;
    }
    [data-testid="stCaptionContainer"] { color: var(--muted); }
    [data-testid="stMetric"] { background: transparent; border: 0; padding: 0; min-height: 0; }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    [data-testid="stMetricValue"] { color: var(--text); font-size: 1.55rem; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--line);
        background: rgba(25, 26, 22, .78);
        border-radius: 5px;
    }
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background: #171813; color: var(--text); border-color: #45473b;
        border-radius: 4px;
    }
    [data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {
        border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent);
    }
    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder {
        color: #b8b7ab !important; opacity: 1;
    }
    .stButton > button, [data-testid="stFormSubmitButton"] button {
        min-height: 48px; height: auto; white-space: normal; overflow: visible;
        overflow-wrap: anywhere; line-height: 1.35; padding: .65rem .9rem;
        border-radius: 4px; border: 1px solid #4a4b40;
        background: #22231d; color: #f4f2e9; font-weight: 650;
        transition: background .16s ease, border-color .16s ease;
    }
    .stButton > button:hover, [data-testid="stFormSubmitButton"] button:hover {
        background: #2c2e25; border-color: var(--accent-deep); color: #ffffff;
    }
    .stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] {
        min-height: 50px; background: var(--accent); border-color: var(--accent); color: #11120f;
        font-size: .96rem; font-weight: 750;
    }
    .stButton > button[kind="primary"]:hover,
    [data-testid="stFormSubmitButton"] button[kind="primary"]:hover { background: #e0f98a; border-color: #e0f98a; color: #11120f; }
    .stButton > button:focus-visible,
    [data-testid="stFormSubmitButton"] button:focus-visible,
    [data-testid="stSidebar"] [data-testid="stRadioOption"]:focus-within > div {
        outline: 2px solid var(--accent); outline-offset: 2px;
    }
    .stButton > button:disabled,
    [data-testid="stFormSubmitButton"] button:disabled {
        background: #292a24; border-color: #57584d; color: #d1d0c5;
        opacity: 1; cursor: not-allowed;
    }
    [data-testid="stProgressBar"] > div > div { background: var(--accent); }
    .topbar {
        display:flex; align-items:center; justify-content:space-between; gap:1rem;
        border-bottom:1px solid var(--line); padding:0 0 1.05rem; margin-bottom:2.1rem;
    }
    .brand { display:flex; align-items:center; gap:.8rem; }
    .brand-mark {
        width:38px; height:38px; display:grid; place-items:center; border-radius:5px;
        color:var(--accent); font:700 .8rem 'Cascadia Code', monospace;
        background:#20211a; border:1px solid #555a38;
    }
    .brand-name { color:var(--text); font-size:1rem; font-weight:720; }
    .brand-sub { color:var(--muted); font-size:.78rem; margin-top:2px; }
    .status-group { display:flex; flex-wrap:wrap; justify-content:flex-end; gap:.55rem; }
    .status-pill, .eyebrow, .tag {
        display:inline-flex; align-items:center; gap:.42rem; border:1px solid var(--line);
        border-radius:3px; padding:.34rem .62rem; color:#c9c8bd; font-size:.74rem;
        text-transform:uppercase; letter-spacing:.045em;
    }
    .dot { width:7px; height:7px; display:inline-block; border-radius:50%; background:var(--green); }
    .dot.off { background:var(--amber); }
    .page-intro { margin:0 0 1.7rem; padding:0 0 1.1rem; border-bottom:1px solid var(--line); }
    .page-intro p { color:var(--muted); margin:.45rem 0 0; font-size:1rem; }
    .section-label { color:var(--accent); font:650 .72rem 'Cascadia Code', monospace; text-transform:uppercase; letter-spacing:.045em; }
    .panel {
        background:var(--surface); border:1px solid var(--line); border-radius:8px;
        padding:1.05rem 1.15rem; margin-bottom:.8rem;
    }
    .panel-title { display:flex; justify-content:space-between; align-items:center; gap:.6rem; color:var(--text); font-weight:680; margin-bottom:.58rem; }
    .panel-copy { color:#c2d0d7; line-height:1.58; white-space:pre-wrap; overflow-wrap:anywhere; }
    .subtle { color:var(--muted); font-size:.86rem; }
    .evidence-panel { border-left:2px solid #898b78; }
    .recommend-panel { border-left:2px solid var(--accent); background:#202219; }
    .warning-panel { border-left:3px solid var(--amber); }
    .severity { color:#ffb4a9; background:#3a2222; border-color:#70413d; text-transform:uppercase; }
    .step-row { display:flex; gap:.85rem; align-items:flex-start; padding:.65rem 0; border-bottom:1px solid #34362e; }
    .step-row:last-child { border-bottom:0; }
    .step-number { color:var(--accent); font:650 .76rem 'Cascadia Code', monospace; min-width:1.6rem; }
    .memory-label { color:#4c512e; font:650 .72rem 'Cascadia Code', monospace; letter-spacing:.045em; overflow-wrap:anywhere; }
    .memory-card {
        position:relative; display:grid; grid-template-columns:42px 1fr; gap:1rem;
        padding:1.05rem 1.15rem; margin:.65rem 0; color:#26271f;
        background:var(--paper); border:1px solid #b9b8a9; border-radius:4px;
        box-shadow:0 8px 26px rgba(0,0,0,.12); transition:transform .18s ease, border-color .18s ease;
    }
    .memory-card:hover { transform:translateY(-2px); border-color:var(--accent-deep); }
    .memory-card p { color:#45463c; margin:.45rem 0 0; line-height:1.5; white-space:pre-wrap; overflow-wrap:anywhere; }
    .memory-index { display:grid; place-items:center; align-self:start; width:34px; height:34px; color:#27291f; background:var(--accent); border-radius:3px; font:650 .68rem 'Cascadia Code', monospace; }
    .memory-heading { color:#20211b; margin:.22rem 0 .5rem; font-size:1.08rem; font-weight:700; }
    .memory-service { color:#68695d; font-size:.82rem; }
    .memory-fields { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:.6rem .9rem; margin-top:.8rem; }
    .memory-field { padding-top:.5rem; border-top:1px solid #c9c8ba; }
    .memory-field b { display:block; color:#66684f; font:600 .68rem 'Cascadia Code',monospace; text-transform:uppercase; margin-bottom:.23rem; overflow-wrap:anywhere; }
    .memory-field span { color:#292a22; font-size:.84rem; line-height:1.4; overflow-wrap:anywhere; }
    .memory-route { display:flex; align-items:center; flex-wrap:wrap; gap:.5rem; margin:.7rem 0 1rem; color:#c9c8bd; font:600 .7rem 'Cascadia Code',monospace; text-transform:uppercase; }
    .memory-route span { padding:.48rem .6rem; border:1px solid #424439; background:#181914; overflow-wrap:anywhere; }
    .memory-route i { color:var(--accent); font-style:normal; }
    .loop { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); margin:1.2rem 0 1.7rem; padding:.85rem 0; border-top:1px solid #494b3e; border-bottom:1px solid #494b3e; background:linear-gradient(90deg,rgba(213,243,106,.055),transparent 75%); }
    .loop-step { padding:.35rem .75rem; position:relative; border-right:1px solid #36382e; }
    .loop-step:last-child { border:0; }
    .loop-step b { display:block; color:var(--accent); font:600 .72rem 'Cascadia Code',monospace; margin-bottom:.4rem; overflow-wrap:anywhere; }
    .loop-step span { color:#dddcd2; font-size:.82rem; }
    .overview-stat { min-height:84px; padding:.15rem .7rem .65rem 0; border-bottom:1px solid #414238; }
    .overview-stat b { display:block; font-size:1.55rem; font-weight:600; color:var(--text); margin:.45rem 0 .28rem; }
    .overview-stat span { color:var(--muted); font:600 .72rem 'Cascadia Code',monospace; text-transform:uppercase; overflow-wrap:anywhere; }
    .memory-signal { border-left:2px solid var(--accent); padding:.1rem 0 .2rem .85rem; margin:.85rem 0; }
    .memory-signal b { display:block; color:var(--text); font-weight:620; }
    .memory-signal span { color:var(--muted); font-size:.84rem; }
    [data-testid="stSidebar"] [data-testid="stRadioOption"] { color:#d4d2c7; cursor:pointer; }
    [data-testid="stSidebar"] [data-testid="stRadioOption"] > div {
        min-height:42px; height:auto; padding:.48rem .62rem; border:1px solid transparent;
        border-left:2px solid transparent; border-radius:3px; overflow:visible;
        transition:background .14s ease, border-color .14s ease;
    }
    [data-testid="stSidebar"] [data-testid="stRadioOption"] > div p {
        color:#d4d2c7; font-size:.94rem; line-height:1.4;
    }
    [data-testid="stSidebar"] [data-testid="stRadioOption"]:hover > div {
        background:#20211b; border-color:#34362e;
    }
    [data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] > div {
        background:#25271e; border-color:#474a38; border-left-color:var(--accent);
    }
    [data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] p {
        color:#f4f2e9; font-weight:700;
    }
    [data-testid="stSidebar"] [data-testid="stRadioOption"] p { margin:0; line-height:1.35; }
    [data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:4px; }
    @media (max-width: 760px) {
        .block-container { padding:1rem 1rem 2rem; }
        .topbar { align-items:flex-start; flex-direction:column; }
        .status-group { justify-content:flex-start; }
        .loop { grid-template-columns:1fr 1fr; }
        .loop-step { border-right:0; border-bottom:1px solid #34362e; }
        .memory-route { align-items:flex-start; flex-direction:column; }
        .memory-route i { transform:rotate(90deg); margin-left:.8rem; }
        .memory-fields { grid-template-columns:1fr; }
        h1 { font-size:2rem; }
    }
    @media (max-width: 520px) {
        .loop { grid-template-columns:1fr; }
        .loop-step { border-right:0; border-bottom:1px solid #34362e; }
        .loop-step:last-child { border-bottom:0; }
        .memory-card { grid-template-columns:30px minmax(0,1fr); gap:.65rem; padding:.9rem; }
        .memory-index { width:28px; height:28px; }
        .status-group { width:100%; }
        .status-pill { white-space:normal; }
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "incident_history" not in st.session_state:
    st.session_state.incident_history = []

if "analysis" not in st.session_state:
    st.session_state.analysis = None

if "memories" not in st.session_state:
    st.session_state.memories = []

if "incident_saved" not in st.session_state:
    st.session_state.incident_saved = False

if "page" not in st.session_state:
    st.session_state.page = "Overview"

if "last_error" not in st.session_state:
    st.session_state.last_error = None


# ============================================================
# CLIENT HELPERS
# ============================================================

def get_hindsight_client():
    if not HINDSIGHT_API_KEY:
        return None

    return Hindsight(
        base_url=HINDSIGHT_BASE_URL,
        api_key=HINDSIGHT_API_KEY
    )


@st.cache_resource
def get_groq_client():
    if not GROQ_API_KEY:
        return None

    return Groq(api_key=GROQ_API_KEY)


# ============================================================
# HINDSIGHT RECALL
# ============================================================

def recall_incident_experience(incident_text):

    client = get_hindsight_client()

    if client is None:
        return []

    query = f"""
    Find historical production incidents similar to this new incident.

    New incident:
    {incident_text}

    Focus on:
    - similar symptoms
    - affected services
    - root causes
    - investigation approaches
    - successful remediation
    - failed approaches
    - resolution time
    - lessons learned
    """

    try:
        result = client.recall(
            bank_id=HINDSIGHT_BANK_ID,
            query=query,
            max_tokens=5000,
            budget="high"
        )

        memories = []

        for memory in result.results:
            memories.append(
                {
                    "type": memory.type,
                    "text": memory.text
                }
            )

        return memories
    finally:
        client.close()


# ============================================================
# GROQ ANALYSIS
# ============================================================

def analyze_incident(incident_text, memories):

    groq_client = get_groq_client()

    if groq_client is None:
        return {
            "summary": "Groq API key is missing.",
            "severity": "Unknown",
            "likely_root_cause": "Unable to analyze.",
            "investigation_steps": [],
            "recommended_action": "Configure GROQ_API_KEY.",
            "confidence": "Low",
            "evidence": []
        }

    memory_text = "\n\n".join(
        [
            f"Historical Memory {i + 1}:\n{m['text']}"
            for i, m in enumerate(memories)
        ]
    )

    prompt = f"""
You are an expert Site Reliability Engineer and incident commander.

You are investigating a NEW production incident.

NEW INCIDENT:
{incident_text}

HISTORICAL INCIDENT EXPERIENCE FROM HINDSIGHT:
{memory_text if memory_text else "No relevant historical incidents found."}

Your job is to reason from the historical evidence.

IMPORTANT:
- Do not invent historical incidents.
- Do not claim something is certain unless evidence supports it.
- Clearly distinguish historical evidence from your own inference.
- Prefer actions that succeeded in similar historical incidents.
- Mention failed approaches when historical evidence indicates them.
- Give practical investigation steps.
- Keep the response concise enough for an incident commander.

Return ONLY valid JSON in this exact structure:

{{
    "summary": "short incident summary",
    "severity": "SEV-1 / SEV-2 / SEV-3 / SEV-4",
    "likely_root_cause": "most likely cause and whether it is evidence-backed or inferred",
    "investigation_steps": [
        "step 1",
        "step 2",
        "step 3",
        "step 4"
    ],
    "recommended_action": "recommended immediate remediation",
    "confidence": "High / Medium / Low",
    "evidence": [
        "historical evidence 1",
        "historical evidence 2"
    ]
}}
"""

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": "You are a production reliability expert."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response.choices[0].message.content.strip()

    # Remove accidental markdown fences
    if content.startswith("```"):
        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "summary": content,
            "severity": "Unknown",
            "likely_root_cause": "AI returned non-JSON analysis.",
            "investigation_steps": [
                "Review application logs",
                "Review database metrics",
                "Review recent deployments",
                "Check infrastructure health"
            ],
            "recommended_action": "Investigate using the historical memories shown below.",
            "confidence": "Medium",
            "evidence": []
        }


# ============================================================
# RETAIN INCIDENT OUTCOME
# ============================================================

def save_incident_to_memory(
    incident_text,
    analysis,
    resolution,
    outcome,
    resolution_time
):

    client = get_hindsight_client()

    if client is None:
        return False

    content = f"""
    Incident Response Record

    Incident:
    {incident_text}

    AI Analysis:
    {analysis}

    Resolution:
    {resolution}

    Outcome:
    {outcome}

    Resolution Time:
    {resolution_time}

    This incident should be remembered for future incident-response
    investigations. Preserve symptoms, root cause, investigation path,
    remediation, outcome, resolution time, successful actions,
    unsuccessful actions, and lessons learned.
    """

    try:
        client.retain(
            bank_id=HINDSIGHT_BANK_ID,
            content=content,
            context="production incident postmortem"
        )

        return True
    finally:
        client.close()


# ============================================================
# UI HELPERS
# ============================================================

def render_memory_cards(memories, limit=None):
    displayed = memories if limit is None else memories[:limit]
    for index, memory in enumerate(displayed, start=1):
        text = str(memory.get("text", "No memory text was returned."))
        fields = extract_memory_fields(text)
        heading = fields.get("incident_id", "Recalled experience")
        service = fields.get("service", "")
        details = [
            ("Root cause", fields.get("root_cause")),
            ("Resolution", fields.get("resolution")),
            ("Time to resolve", fields.get("resolution_time")),
            ("Outcome / lesson", fields.get("outcome") or fields.get("lesson_learned") or fields.get("successful_action"))
        ]
        detail_html = "".join(
            f'<div class="memory-field"><b>{escape(label)}</b><span>{escape(value)}</span></div>'
            for label, value in details if value
        )
        if not detail_html:
            detail_html = f'<p>{escape(text)}</p>'
        st.markdown(
            f'<article class="memory-card"><div class="memory-index">{index:02}</div>'
            '<div><div class="memory-label">HINDSIGHT MEMORY · RECALLED EXPERIENCE</div>'
            f'<div class="memory-heading">{escape(heading)}</div>'
            f'<div class="memory-service">{escape(service or memory.get("type", "Past incident experience").replace("_", " ").title())}</div>'
            f'<div class="memory-fields">{detail_html}</div></div></article>',
            unsafe_allow_html=True
        )


def extract_memory_fields(text):
    labels = {
        "incident id": "incident_id",
        "service": "service",
        "root cause": "root_cause",
        "resolution": "resolution",
        "resolution time": "resolution_time",
        "outcome": "outcome",
        "lesson learned": "lesson_learned",
        "successful action": "successful_action"
    }
    pattern = re.compile(r"^\s*(Incident ID|Service|Root Cause|Resolution Time|Resolution|Outcome|Lesson Learned|Successful Action)\s*:\s*(.*)$", re.IGNORECASE)
    fields = {}
    active_field = None
    for line in text.splitlines():
        match = pattern.match(line)
        if match:
            active_field = labels[match.group(1).casefold()]
            fields[active_field] = match.group(2).strip()
        elif active_field and line.strip():
            fields[active_field] += "\n" + line.strip()
    return fields


def resolution_minutes(value):
    match = re.search(r"(\d+(?:\.\d+)?)\s*(seconds?|secs?|s|minutes?|mins?|m|hours?|hrs?|h)\b", str(value), re.IGNORECASE)
    if not match:
        return None
    amount = float(match.group(1))
    unit = match.group(2).casefold()
    if unit.startswith("h"):
        return amount * 60
    if unit.startswith("s"):
        return amount / 60
    return amount


def average_resolution_label(history):
    durations = [resolution_minutes(item.get("resolution_time", "")) for item in history]
    durations = [duration for duration in durations if duration is not None]
    if not durations:
        return "Not recorded"
    average = sum(durations) / len(durations)
    return f"{average:.0f} min" if average.is_integer() else f"{average:.1f} min"


def render_memory_loop(steps=None):
    if steps is None:
        steps = [
        ("01 · NEW INCIDENT", "Capture symptoms and impact"),
        ("02 · RECALL", "Find related experience"),
        ("03 · INVESTIGATE", "Use evidence to guide checks"),
        ("04 · RESOLVE", "Record the verified fix"),
        ("05 · LEARN", "Make the next response smarter")
        ]
    columns = "".join(
        f'<div class="loop-step"><b>{escape(label)}</b><span>{escape(description)}</span></div>'
        for label, description in steps
    )
    st.markdown(f'<div class="loop">{columns}</div>', unsafe_allow_html=True)


def safe_error_text(error):
    message = f"{type(error).__name__}: {error}"
    for secret in (HINDSIGHT_API_KEY, GROQ_API_KEY):
        if secret:
            message = message.replace(secret, "[redacted]")
    return message


def render_steps(steps):
    if not steps:
        st.caption("No investigation steps were returned.")
        return
    for index, step in enumerate(steps, start=1):
        st.markdown(
            f'<div class="step-row"><span class="step-number">{index:02}</span>'
            f'<span>{escape(str(step))}</span></div>',
            unsafe_allow_html=True
        )


def make_incident_text(incident_id, service, symptoms, impact, recent_changes):
    return f"""Incident ID: {incident_id}

Service: {service}

Symptoms:
{symptoms}

Customer Impact:
{impact}

Recent Changes / Context:
{recent_changes}"""


def run_investigation(incident_text):
    st.session_state.last_error = None
    try:
        with st.spinner("Searching incident memory for relevant experience..."):
            memories = recall_incident_experience(incident_text)
    except Exception as error:
        memories = []
        st.session_state.last_error = safe_error_text(error)

    try:
        with st.spinner("Comparing historical experiences and analyzing root-cause patterns..."):
            analysis = analyze_incident(incident_text, memories)
    except Exception as error:
        st.session_state.last_error = safe_error_text(error)
        analysis = None

    st.session_state.memories = memories
    st.session_state.analysis = analysis
    st.session_state.current_incident = incident_text
    st.session_state.incident_saved = False


def render_investigation_result(analysis, memories):
    st.markdown("### Investigation assessment")
    severity, confidence, remembered = st.columns(3)
    severity.metric("Severity", analysis.get("severity", "Unknown"))
    confidence.metric("Confidence", analysis.get("confidence", "Unknown"))
    remembered.metric("Recalled experiences", len(memories))

    left, right = st.columns([1.05, .95], gap="large")
    with left:
        with st.container(border=True):
            st.markdown('<div class="section-label">AI Assessment</div>', unsafe_allow_html=True)
            st.markdown("#### Incident summary")
            st.write(analysis.get("summary", "No summary available."))
            st.markdown("#### Likely root cause")
            st.write(analysis.get("likely_root_cause", "No root cause identified."))
        with st.container(border=True):
            st.markdown('<div class="section-label">AI Reasoning</div>', unsafe_allow_html=True)
            st.markdown("#### Recommended investigation path")
            render_steps(analysis.get("investigation_steps", []))
    with right:
        with st.container(border=True):
            st.markdown('<div class="section-label">Recommended Action</div>', unsafe_allow_html=True)
            st.markdown("#### Immediate next move")
            st.write(analysis.get("recommended_action", "No recommendation available."))
        with st.container(border=True):
            st.markdown('<div class="section-label">Historical Evidence</div>', unsafe_allow_html=True)
            evidence = analysis.get("evidence", [])
            if evidence:
                for item in evidence:
                    st.markdown(f"- {item}")
            else:
                st.caption("The model returned no explicit historical evidence. Validate recommendations against live telemetry.")
        with st.container(border=True):
            st.markdown('<div class="section-label">Uncertainty</div>', unsafe_allow_html=True)
            st.write("This assessment is a diagnostic hypothesis. Confirm the root cause with service telemetry before remediation.")

    st.markdown("### Relevant past experience")
    if memories:
        incident_meta = st.session_state.get("current_incident_meta", {})
        current_label = " · ".join(filter(None, [incident_meta.get("incident_id"), incident_meta.get("service")]))
        st.markdown(
            '<div class="memory-route">'
            f'<span>CURRENT INCIDENT<br><b>{escape(current_label or "Current investigation")}</b></span>'
            '<i>→</i><span>SIMILAR EXPERIENCE</span><i>→</i>'
            '<span>RECALLED MEMORY</span><i>→</i><span>INVESTIGATION PATH</span></div>',
            unsafe_allow_html=True
        )
        render_memory_cards(memories, limit=5)
        st.caption("The recommendation is informed by the recalled context above; similarity is not proof of a shared root cause.")
    else:
        st.info("No relevant Hindsight memory was returned for this incident. The assessment is based on the current incident details only.")


# ============================================================
# APPLICATION SHELL AND NAVIGATION
# ============================================================

with st.sidebar:
    st.markdown("### Incident Response Agent")
    st.caption("AI incident command center")
    st.markdown("---")
    pages = ["Overview", "Investigate", "Incident History", "Memory", "Experience", "Demo Mode"]
    st.radio("Workspace", pages, key="page", label_visibility="collapsed")
    st.markdown("---")
    st.caption("MEMORY BANK")
    st.code(HINDSIGHT_BANK_ID, language=None)
    st.caption("New incidents are recalled from Hindsight before Groq generates an investigation path.")

hindsight_ready = bool(HINDSIGHT_API_KEY)
groq_ready = bool(GROQ_API_KEY)
st.markdown(
    '<div class="topbar"><div class="brand"><div class="brand-mark">IR</div>'
    '<div><div class="brand-name">Incident Response Agent</div>'
    '<div class="brand-sub">Memory-driven AI incident intelligence</div></div></div>'
    '<div class="status-group">'
    f'<span class="status-pill"><i class="dot {"" if hindsight_ready else "off"}"></i>Hindsight {"configured" if hindsight_ready else "not configured"}</span>'
    f'<span class="status-pill"><i class="dot {"" if groq_ready else "off"}"></i>AI engine {"configured" if groq_ready else "not configured"}</span>'
    '</div></div>',
    unsafe_allow_html=True
)

history = st.session_state.incident_history
recalled_count = len(st.session_state.memories)
current_page = st.session_state.page


# ============================================================
# OVERVIEW
# ============================================================

if current_page == "Overview":
    st.markdown('<div class="page-intro"><div class="section-label">AI INCIDENT COMMAND CENTER</div><h1>Incident Response Agent</h1><p>Turn incident history into operational intelligence.</p></div>', unsafe_allow_html=True)
    recurring_causes = {}
    for incident in history:
        cause = incident.get("root_cause", "").strip()
        if cause and cause.casefold() not in {"unknown", "not recorded", "not confirmed"}:
            recurring_causes[cause] = recurring_causes.get(cause, 0) + 1
    recurring_patterns = [cause for cause, count in recurring_causes.items() if count > 1]
    overview_stats = [
        ("01 / ACTIVE", 1 if st.session_state.analysis and not st.session_state.incident_saved else 0),
        ("02 / RESOLVED", len(history)),
        ("03 / AVG. RESOLUTION", average_resolution_label(history)),
        ("04 / MEMORIES RECALLED", recalled_count),
        ("05 / RECURRING PATTERNS", len(recurring_patterns))
    ]
    metric_cols = st.columns(5)
    for column, (label, value) in zip(metric_cols, overview_stats):
        column.markdown(
            f'<div class="overview-stat"><span>{escape(label)}</span><b>{escape(str(value))}</b></div>',
            unsafe_allow_html=True
        )

    render_memory_loop()

    recent_col, insights_col = st.columns([1.35, .85], gap="large")
    with recent_col:
        st.markdown("### Recent incident experience")
        if history:
            for incident in reversed(history[-5:]):
                with st.container(border=True):
                    head, status = st.columns([3, 1])
                    head.markdown(f"**{incident['incident_id']}** · {incident['service']}")
                    status.markdown('<span class="tag">RESOLVED</span>', unsafe_allow_html=True)
                    st.caption(f"Root cause: {incident.get('root_cause', 'Recorded in analysis')} · Resolution time: {incident.get('resolution_time') or 'Not recorded'}")
        else:
            with st.container(border=True):
                st.markdown("#### No incident experience yet")
                st.write("Investigate an incident, capture its resolution, and the experience will appear here.")
                st.button("Start an investigation", on_click=lambda: st.session_state.update(page="Investigate"))
    with insights_col:
        st.markdown("### Live incident intelligence")
        if st.session_state.memories:
            with st.container(border=True):
                st.markdown("### Memory signals")
                st.markdown(f'<div class="memory-signal"><b>{recalled_count} experience(s) recalled</b><span>Returned by Hindsight for the latest investigation.</span></div>', unsafe_allow_html=True)
                memory_fields = extract_memory_fields(str(st.session_state.memories[0].get("text", "")))
                signal = memory_fields.get("root_cause") or memory_fields.get("successful_action")
                if signal:
                    st.markdown(f'<div class="memory-signal"><b>Prior signal</b><span>{escape(signal)}</span></div>', unsafe_allow_html=True)
                st.button("Review incident memory", on_click=lambda: st.session_state.update(page="Memory"))
        else:
            with st.container(border=True):
                st.markdown("### Memory signals")
                st.markdown('<div class="memory-signal"><b>No recall in this session</b><span>Investigate an incident to search the persistent Hindsight bank.</span></div>', unsafe_allow_html=True)
                st.button("Investigate an incident", on_click=lambda: st.session_state.update(page="Investigate"), type="primary")
        with st.container(border=True):
            st.markdown("### Recurring patterns")
            if recurring_patterns:
                for pattern in recurring_patterns:
                    st.markdown(f'<div class="memory-signal"><b>Repeated root-cause assessment</b><span>{escape(pattern)} · {recurring_causes[pattern]} captured incidents</span></div>', unsafe_allow_html=True)
            else:
                st.caption("Patterns appear here when the same root-cause assessment is captured more than once.")


# ============================================================
# INVESTIGATE
# ============================================================

elif current_page == "Investigate":
    st.markdown('<div class="page-intro"><h1>Investigate Incident</h1><p>Use historical incident experience to accelerate diagnosis, without mistaking similarity for certainty.</p></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="section-label">New incident</div>', unsafe_allow_html=True)
        id_col, service_col = st.columns(2)
        incident_id = id_col.text_input("Incident ID", value="INC-002", key="investigate_id")
        service = service_col.text_input("Affected service", value="Production Orders API", key="investigate_service")
        symptoms_col, impact_col = st.columns(2)
        symptoms = symptoms_col.text_area("Symptoms", value="Orders API latency has increased and requests are becoming slow.", height=112, key="investigate_symptoms")
        impact = impact_col.text_area("Business / customer impact", value="Customers are experiencing slow order operations.", height=112, key="investigate_impact")
        recent_changes = st.text_area("Recent changes / context", value="No known deployment. Database query latency appears elevated.", height=92, key="investigate_changes")
        investigate = st.button("Investigate with Incident Memory", type="primary", width="stretch")

    if investigate:
        if not incident_id.strip() or not service.strip() or not symptoms.strip():
            st.error("Add an incident ID, service, and symptom summary before starting the investigation.")
        else:
            run_investigation(make_incident_text(incident_id, service, symptoms, impact, recent_changes))
            st.session_state.current_incident_meta = {
                "incident_id": incident_id,
                "service": service
            }
            if st.session_state.analysis:
                st.success(f"Investigation ready. Hindsight returned {len(st.session_state.memories)} relevant experience(s).")
                if st.session_state.last_error:
                    st.warning("Historical memory could not be retrieved. The AI assessment is based on current incident details only.")
            else:
                st.error("The AI analysis could not be completed. Verify the AI engine configuration and try again.")
            if st.session_state.last_error:
                with st.expander("Technical details"):
                    st.code(st.session_state.last_error)

    analysis = st.session_state.analysis
    if analysis:
        st.markdown("---")
        render_investigation_result(analysis, st.session_state.memories)
        st.markdown("### Close incident & teach Hindsight")
        st.caption("Record the actual fix and lesson learned. The outcome is retained in persistent incident memory for future recall.")
        with st.container(border=True):
            resolution = st.text_area("Resolution", placeholder="What actually fixed the incident?", height=88, key="resolution_text")
            outcome = st.text_area("Outcome / lesson learned", placeholder="What should responders check earlier next time?", height=82, key="resolution_outcome")
            time_col, save_col = st.columns([1, 2])
            resolution_time = time_col.text_input("Resolution time", placeholder="e.g. 18 minutes", key="resolution_time")
            save_button = save_col.button("Resolve & Teach Hindsight", type="primary", width="stretch", disabled=st.session_state.incident_saved)
            render_memory_loop([
                ("01 · RESOLVE", "Record the verified fix"),
                ("02 · CAPTURE", "Save the outcome"),
                ("03 · STORE", "Retain in Hindsight"),
                ("04 · REUSE", "Inform the next response")
            ])

        if save_button:
            if not resolution.strip():
                st.error("Enter the resolution before storing this incident experience.")
            else:
                try:
                    with st.spinner("Capturing the outcome and storing incident experience in Hindsight..."):
                        saved = save_incident_to_memory(st.session_state.current_incident, analysis, resolution, outcome, resolution_time)
                except Exception as error:
                    saved = False
                    st.session_state.last_error = safe_error_text(error)
                if saved:
                    incident_meta = st.session_state.get("current_incident_meta", {})
                    st.session_state.incident_history.append({
                        "incident_id": incident_meta.get("incident_id", incident_id),
                        "service": incident_meta.get("service", service),
                        "severity": analysis.get("severity", "Unknown"),
                        "root_cause": analysis.get("likely_root_cause", "Not confirmed"),
                        "resolution_time": resolution_time,
                        "resolution": resolution,
                        "outcome": outcome,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    st.session_state.incident_saved = True
                    st.success("Incident resolved and retained in Hindsight memory.")
                else:
                    st.error("Unable to store this incident experience. Check the Hindsight configuration and connection.")
                    if st.session_state.last_error:
                        with st.expander("Technical details"):
                            st.code(st.session_state.last_error)


# ============================================================
# INCIDENT HISTORY
# ============================================================

elif current_page == "Incident History":
    st.markdown('<div class="page-intro"><h1>Incident History</h1><p>Review outcomes captured during this application session.</p></div>', unsafe_allow_html=True)
    if not history:
        with st.container(border=True):
            st.markdown("#### No captured incidents in this session")
            st.write("Resolved incidents are listed here after their outcomes are retained. Historical experience remains available through Hindsight recall.")
            st.button("Investigate an incident", on_click=lambda: st.session_state.update(page="Investigate"), type="primary")
    else:
        search = st.text_input("Search incidents", placeholder="Filter by ID, service, root cause, or resolution")
        services = sorted({item["service"] for item in history})
        service_filter = st.selectbox("Service", ["All services"] + services)
        filtered = [item for item in history if (service_filter == "All services" or item["service"] == service_filter)]
        if search.strip():
            query = search.casefold()
            filtered = [item for item in filtered if query in " ".join(str(value) for value in item.values()).casefold()]
        st.dataframe([
            {"Incident ID": item["incident_id"], "Service": item["service"], "Severity": item["severity"], "Root cause": item["root_cause"], "Status": "Resolved", "Resolution time": item["resolution_time"] or "Not recorded", "Date": item["date"]}
            for item in filtered
        ], width="stretch", hide_index=True)
        if filtered:
            selected_id = st.selectbox("Open incident experience", [item["incident_id"] for item in filtered])
            selected = next(item for item in filtered if item["incident_id"] == selected_id)
            with st.container(border=True):
                st.markdown(f"#### {selected['incident_id']} · {selected['service']}")
                st.caption(f"{selected['date']} · {selected['severity']} · {selected['resolution_time'] or 'Resolution time not recorded'}")
                st.markdown("**Root cause assessment**")
                st.write(selected["root_cause"])
                st.markdown("**Resolution**")
                st.write(selected["resolution"])
                if selected.get("outcome"):
                    st.markdown("**Lesson learned**")
                    st.write(selected["outcome"])


# ============================================================
# MEMORY
# ============================================================

elif current_page == "Memory":
    st.markdown('<div class="page-intro"><h1>Incident Memory</h1><p>Persistent experience links prior incidents to the investigation happening now.</p></div>', unsafe_allow_html=True)
    memory_metrics = st.columns(4)
    memory_metrics[0].metric("Current recall", recalled_count)
    memory_metrics[1].metric("Retained this session", len(history))
    memory_metrics[2].metric("Successful outcomes", "Not classified")
    memory_metrics[3].metric("Average resolution", "Not normalized")
    render_memory_loop([
        ("01 · INCIDENT", "Symptoms and service context"),
        ("02 · INVESTIGATE", "Actions and root-cause evidence"),
        ("03 · RESOLVE", "What restored service"),
        ("04 · LEARN", "What to repeat or avoid"),
        ("05 · RECALL", "Useful context next time")
    ])
    st.markdown("### Relevant past experience")
    if st.session_state.memories:
        st.caption("These are the actual memory records returned by the latest Hindsight recall.")
        render_memory_cards(st.session_state.memories)
    else:
        with st.container(border=True):
            st.markdown("#### No recalled experience in this session")
            st.write("Start an investigation to search the persistent Hindsight bank. Resolve an incident to add a new experience.")
            st.button("Search incident memory", on_click=lambda: st.session_state.update(page="Investigate"), type="primary")
    if history:
        st.markdown("### Recently retained in this session")
        for item in reversed(history):
            with st.container(border=True):
                st.markdown(f"**{item['incident_id']} · {item['service']}**")
                st.caption(f"Retained after resolution · {item['date']}")
                st.write(item["resolution"])


# ============================================================
# EXPERIENCE
# ============================================================

elif current_page == "Experience":
    st.markdown('<div class="page-intro"><h1>Incident Experience</h1><p>Patterns derived from incident outcomes captured in this session. Persistent-bank-wide analytics are not exposed by the current backend.</p></div>', unsafe_allow_html=True)
    if not history:
        with st.container(border=True):
            st.markdown("#### Experience analytics will appear here")
            st.write("Retain resolved incidents to build a grounded view of services, root causes, and remediation outcomes.")
            st.button("Capture incident experience", on_click=lambda: st.session_state.update(page="Investigate"), type="primary")
    else:
        service_counts = {}
        cause_counts = {}
        for item in history:
            service_counts[item["service"]] = service_counts.get(item["service"], 0) + 1
            cause = item.get("root_cause", "Not recorded")
            cause_counts[cause] = cause_counts.get(cause, 0) + 1
        exp_metrics = st.columns(3)
        exp_metrics[0].metric("Captured outcomes", len(history))
        exp_metrics[1].metric("Services represented", len(service_counts))
        exp_metrics[2].metric("Distinct root-cause assessments", len(cause_counts))
        chart_col, causes_col = st.columns(2, gap="large")
        with chart_col:
            st.markdown("### Captured incidents by service")
            st.bar_chart(
                [{"Service": service, "Incidents": count} for service, count in service_counts.items()],
                x="Service",
                y="Incidents",
                y_label="Incidents"
            )
        with causes_col:
            st.markdown("### Root-cause assessments")
            st.dataframe([{"Assessment": cause, "Incidents": count} for cause, count in sorted(cause_counts.items(), key=lambda pair: pair[1], reverse=True)], width="stretch", hide_index=True)
        st.caption("These counts describe this session's captured resolutions; they do not represent a complete Hindsight bank inventory.")


# ============================================================
# DEMO MODE
# ============================================================

elif current_page == "Demo Mode":
    st.markdown('<div class="page-intro"><h1>Memory-Driven Incident Demo</h1><p>Show how persistent incident experience can make a similar future investigation more informed.</p></div>', unsafe_allow_html=True)
    render_memory_loop([
        ("01 · WITHOUT EXPERIENCE", "A new incident starts with limited context"),
        ("02 · RESOLVE + RETAIN", "Capture the verified outcome in Hindsight"),
        ("03 · WITH EXPERIENCE", "Recall context for the next similar incident")
    ])
    with st.container(border=True):
        st.markdown('<div class="section-label">Live memory recall</div>', unsafe_allow_html=True)
        st.caption("This demo uses the configured Hindsight and Groq services. It does not seed fabricated incident history.")
        demo_incident = st.text_area("Incident to investigate", value="Orders API latency has increased significantly.\nCustomers are reporting slow order requests.\nDatabase query latency appears elevated.\nThere was no recent application deployment.", height=130, key="demo_incident")
        run_demo = st.button("Run Memory-Driven Demo", type="primary", width="stretch")
    if run_demo:
        st.session_state.demo_error = None
        with st.status("New incident received", expanded=True) as demo_status:
            st.write("Searching incident memory...")
            try:
                demo_memories = recall_incident_experience(demo_incident)
                st.write("Comparing historical experiences...")
                demo_analysis = analyze_incident(demo_incident, demo_memories)
                st.session_state.demo_memories = demo_memories
                st.session_state.demo_analysis = demo_analysis
                demo_status.update(label="Recommendation improved with recalled experience" if demo_memories else "Investigation completed without a relevant memory", state="complete")
            except Exception as error:
                st.session_state.demo_error = safe_error_text(error)
                demo_status.update(label="Demo could not complete", state="error")
        if st.session_state.get("demo_error"):
            st.error("Unable to complete the demo. Check Hindsight and AI engine configuration.")
            with st.expander("Technical details"):
                st.code(st.session_state.demo_error)
    if st.session_state.get("demo_analysis"):
        demo_memories = st.session_state.get("demo_memories", [])
        demo_analysis = st.session_state.demo_analysis
        status_col, count_col = st.columns([2, 1])
        status_col.markdown("**MEMORY FOUND**" if demo_memories else "**NO MATCHING MEMORY RETURNED**")
        count_col.metric("Experiences recalled", len(demo_memories))
        demo_left, demo_right = st.columns(2, gap="large")
        with demo_left:
            st.markdown("### Recalled experience")
            if demo_memories:
                render_memory_cards(demo_memories, limit=3)
            else:
                st.info("No relevant past experience was returned. The agent has not fabricated one.")
        with demo_right:
            st.markdown("### Recommendation")
            with st.container(border=True):
                st.write(demo_analysis.get("recommended_action", "No recommendation available."))
                st.markdown("**Assessment**")
                st.write(demo_analysis.get("likely_root_cause", "Unknown"))
            with st.container(border=True):
                render_steps(demo_analysis.get("investigation_steps", []))

st.markdown("---")
st.caption("Incident Response Agent · Persistent incident experience powered by Hindsight")