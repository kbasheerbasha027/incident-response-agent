import os
import json
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
    page_title="Incident Experience AI",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #0b1020;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    .hero {
        padding: 30px;
        border-radius: 20px;
        background: linear-gradient(
            135deg,
            #111827 0%,
            #172554 50%,
            #1e1b4b 100%
        );
        border: 1px solid #334155;
        margin-bottom: 25px;
    }

    .hero-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .hero-subtitle {
        font-size: 17px;
        color: #cbd5e1;
        line-height: 1.6;
    }

    .memory-card {
        padding: 18px;
        border-radius: 15px;
        background: #111827;
        border: 1px solid #334155;
        margin-bottom: 12px;
    }

    .memory-title {
        font-weight: 700;
        font-size: 16px;
    }

    .memory-text {
        color: #cbd5e1;
        margin-top: 7px;
        line-height: 1.5;
    }

    .success-box {
        padding: 18px;
        border-radius: 15px;
        background: #052e1b;
        border: 1px solid #16a34a;
        margin: 10px 0;
    }

    .warning-box {
        padding: 18px;
        border-radius: 15px;
        background: #3f2a05;
        border: 1px solid #f59e0b;
        margin: 10px 0;
    }

    .metric-card {
        padding: 18px;
        border-radius: 15px;
        background: #111827;
        border: 1px solid #334155;
        text-align: center;
    }

    .metric-number {
        font-size: 30px;
        font-weight: 800;
    }

    .metric-label {
        color: #94a3b8;
        font-size: 13px;
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


# ============================================================
# CLIENT HELPERS
# ============================================================

@st.cache_resource
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

    client.retain(
        bank_id=HINDSIGHT_BANK_ID,
        content=content,
        context="production incident postmortem"
    )

    return True


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">🚨 Incident Experience AI</div>
        <div class="hero-subtitle">
            A memory-first incident response agent that learns from
            every production incident and uses past experience to
            improve future investigations.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🧠 Memory Engine")

    st.success("Hindsight Connected")

    st.markdown(
        """
        **Memory Bank**

        `Incident Experience`
        """
    )

    st.markdown("---")

    st.markdown("### 🔄 Learning Loop")

    st.markdown(
        """
        **1.** New Incident  
        ↓  
        **2.** Recall Experience  
        ↓  
        **3.** AI Investigation  
        ↓  
        **4.** Recommend Action  
        ↓  
        **5.** Resolve  
        ↓  
        **6.** Capture Outcome  
        ↓  
        **7.** Hindsight Learns
        """
    )

    st.markdown("---")

    st.caption(
        "Powered by Hindsight + Groq + Streamlit"
    )


# ============================================================
# MAIN TABS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🚨 Investigate",
        "🧠 Memory",
        "📈 Experience",
        "🎬 Demo Mode"
    ]
)


# ============================================================
# TAB 1 — INVESTIGATE
# ============================================================

with tab1:

    st.header("New Production Incident")

    col1, col2 = st.columns(2)

    with col1:

        incident_id = st.text_input(
            "Incident ID",
            value="INC-002"
        )

        service = st.text_input(
            "Affected Service",
            value="Production Orders API"
        )

        symptoms = st.text_area(
            "What is happening?",
            value="Orders API latency has increased and requests are becoming slow.",
            height=120
        )

    with col2:

        impact = st.text_area(
            "Business / Customer Impact",
            value="Customers are experiencing slow order operations.",
            height=120
        )

        recent_changes = st.text_area(
            "Recent Changes / Context",
            value="No known deployment. Database query latency appears elevated.",
            height=120
        )

    investigate = st.button(
        "🔍 Investigate With Incident Memory",
        type="primary",
        use_container_width=True
    )

    if investigate:

        incident_text = f"""
        Incident ID: {incident_id}

        Service: {service}

        Symptoms:
        {symptoms}

        Customer Impact:
        {impact}

        Recent Changes / Context:
        {recent_changes}
        """

        with st.spinner(
            "🧠 Searching historical incident experience..."
        ):

            memories = recall_incident_experience(
                incident_text
            )

        st.session_state.memories = memories

        with st.spinner(
            "🤖 Reasoning over historical evidence..."
        ):

            analysis = analyze_incident(
                incident_text,
                memories
            )

        st.session_state.analysis = analysis

        st.session_state.current_incident = incident_text

        st.session_state.incident_saved = False

        st.success(
            f"Historical experience retrieved: {len(memories)} memories"
        )

    if st.session_state.analysis:

        analysis = st.session_state.analysis

        st.markdown("---")

        st.subheader("🎯 Incident Assessment")

        m1, m2, m3 = st.columns(3)

        with m1:
            st.metric(
                "Severity",
                analysis.get("severity", "Unknown")
            )

        with m2:
            st.metric(
                "Confidence",
                analysis.get("confidence", "Unknown")
            )

        with m3:
            st.metric(
                "Historical Memories",
                len(st.session_state.memories)
            )

        st.markdown("### Incident Summary")

        st.info(
            analysis.get(
                "summary",
                "No summary available."
            )
        )

        st.markdown("### 🧩 Likely Root Cause")

        st.warning(
            analysis.get(
                "likely_root_cause",
                "No root cause identified."
            )
        )

        st.markdown("### 🔎 Recommended Investigation Path")

        steps = analysis.get(
            "investigation_steps",
            []
        )

        for i, step in enumerate(steps, start=1):
            st.markdown(
                f"**{i}.** {step}"
            )

        st.markdown("### ⚡ Recommended Immediate Action")

        st.success(
            analysis.get(
                "recommended_action",
                "No recommendation available."
            )
        )

        st.markdown("### 📚 Historical Evidence")

        evidence = analysis.get("evidence", [])

        if evidence:

            for item in evidence:
                st.markdown(
                    f"- {item}"
                )

        else:

            st.caption(
                "No explicit historical evidence was returned."
            )

        # ----------------------------------------------------
        # RESOLUTION CAPTURE
        # ----------------------------------------------------

        st.markdown("---")

        st.subheader("📝 Close Incident & Teach the Agent")

        resolution = st.text_area(
            "What actually fixed the incident?",
            value="",
            placeholder="Example: Added missing database index and API latency returned to normal.",
            height=100
        )

        outcome = st.text_area(
            "Outcome / Lesson Learned",
            value="",
            placeholder="Example: Database indexes should be checked early for Orders API latency.",
            height=100
        )

        resolution_time = st.text_input(
            "Resolution Time",
            value="18 minutes"
        )

        save_button = st.button(
            "🧠 Resolve & Teach Hindsight",
            type="primary",
            use_container_width=True
        )

        if save_button:

            if not resolution.strip():

                st.error(
                    "Please enter what actually fixed the incident."
                )

            else:

                with st.spinner(
                    "🧠 Writing the incident outcome into long-term memory..."
                ):

                    saved = save_incident_to_memory(
                        st.session_state.current_incident,
                        analysis,
                        resolution,
                        outcome,
                        resolution_time
                    )

                if saved:

                    st.session_state.incident_history.append(
                        {
                            "incident_id": incident_id,
                            "service": service,
                            "resolution_time": resolution_time,
                            "resolution": resolution
                        }
                    )

                    st.session_state.incident_saved = True

                    st.success(
                        "✅ Incident resolved and permanently added to Hindsight memory."
                    )

                    st.balloons()


# ============================================================
# TAB 2 — MEMORY
# ============================================================

with tab2:

    st.header("🧠 Retrieved Incident Experience")

    memories = st.session_state.memories

    if not memories:

        st.info(
            "Run an investigation to retrieve historical incident experience."
        )

    else:

        st.write(
            f"Hindsight returned **{len(memories)} relevant memories**."
        )

        for i, memory in enumerate(memories, start=1):

            st.markdown(
                f"""
                <div class="memory-card">
                    <div class="memory-title">
                        Memory {i} · {memory["type"].upper()}
                    </div>
                    <div class="memory-text">
                        {memory["text"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# TAB 3 — EXPERIENCE DASHBOARD
# ============================================================

with tab3:

    st.header("📈 Incident Experience")

    history = st.session_state.incident_history

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Incidents Captured",
            len(history)
        )

    with c2:
        st.metric(
            "Memory Records",
            len(st.session_state.memories)
        )

    with c3:
        st.metric(
            "Learning Status",
            "ACTIVE"
        )

    st.markdown("---")

    st.subheader("What Makes This Agent Different?")

    features = [
        (
            "🧠 Persistent Memory",
            "Past incidents remain available for future investigations."
        ),
        (
            "🔎 Similar Incident Recall",
            "The agent searches previous incident experience before recommending actions."
        ),
        (
            "🎯 Evidence-Based Reasoning",
            "Recommendations are grounded in retrieved historical experience."
        ),
        (
            "🔄 Outcome Learning",
            "Resolved incidents are written back into Hindsight."
        ),
        (
            "📚 Organizational Experience",
            "The agent turns individual incident knowledge into reusable operational memory."
        ),
        (
            "⚡ Faster Investigation",
            "Future responders can start from proven investigation paths instead of starting from zero."
        )
    ]

    for title, description in features:

        st.markdown(
            f"""
            <div class="memory-card">
                <div class="memory-title">{title}</div>
                <div class="memory-text">{description}</div>
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# TAB 4 — DEMO MODE
# ============================================================

with tab4:

    st.header("🎬 Hackathon Demo Mode")

    st.markdown(
        """
        ### The story to demonstrate

        **Incident 1**

        Production Orders API becomes slow.

        Root cause → missing database index.

        Resolution → add index.

        The agent stores the experience in Hindsight.

        ---

        **Incident 2**

        A similar Orders API latency incident happens.

        The agent searches Hindsight.

        It recalls the previous incident.

        It recommends checking database query performance
        and indexes early.

        ---

        ### The key message

        > The agent doesn't just answer incidents.
        > **It remembers how incidents were solved and uses
        > that experience when the next incident happens.**
        """
    )

    st.markdown("---")

    st.subheader("🧪 Quick Demo Incident")

    demo_incident = st.text_area(
        "Paste a new incident",
        value="""Orders API latency has increased significantly.
Customers are reporting slow order requests.
Database query latency appears elevated.
There was no recent application deployment.""",
        height=150
    )

    if st.button(
        "🚀 Run Memory-Driven Demo",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "Recalling previous incident experience..."
        ):

            demo_memories = recall_incident_experience(
                demo_incident
            )

        with st.spinner(
            "Reasoning over the incident history..."
        ):

            demo_analysis = analyze_incident(
                demo_incident,
                demo_memories
            )

        st.success(
            f"Agent found {len(demo_memories)} historical memories."
        )

        st.markdown("### 🧠 What the Agent Remembered")

        for memory in demo_memories[:5]:

            st.info(
                memory["text"]
            )

        st.markdown("### 🤖 What the Agent Recommends")

        st.success(
            demo_analysis.get(
                "recommended_action",
                "No recommendation available."
            )
        )

        st.markdown("### 🎯 Likely Root Cause")

        st.warning(
            demo_analysis.get(
                "likely_root_cause",
                "Unknown"
            )
        )

        st.markdown("### 🔎 Investigation Path")

        for i, step in enumerate(
            demo_analysis.get(
                "investigation_steps",
                []
            ),
            start=1
        ):

            st.write(
                f"**{i}.** {step}"
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Incident Experience AI • Persistent incident memory powered by Hindsight"
)