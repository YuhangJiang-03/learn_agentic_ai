import contextlib
import io
import time
import traceback
from datetime import datetime

import streamlit as st

from src.pipelines.pipeline import run_research_pipeline

st.set_page_config(page_title="Research Studio", page_icon="🔎", layout="wide")

STEPS = [
    ("🔍", "Search", "Finding recent, reliable sources"),
    ("📄", "Read", "Scraping the most relevant page"),
    ("✍️", "Write", "Drafting the research report"),
    ("🧐", "Critique", "Reviewing the draft for quality"),
]
EXAMPLES = [
    "The impact of AI on the job market in 2026",
    "State of solid-state battery technology",
    "How do mRNA vaccines work?",
    "Trends in renewable energy investment",
]

st.markdown(
    """
    <style>
      .block-container {padding-top: 2rem; max-width: 1200px;}
      .hero {padding: 1.6rem 1.8rem; border-radius: 16px; color: #fff; margin-bottom: 1.2rem;
             background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 55%, #db2777 100%);}
      .hero h1 {margin: 0; font-size: 2rem; color: #fff;}
      .hero p {margin: .3rem 0 0; opacity: .9;}
      .step {display: flex; gap: .8rem; align-items: center; padding: .7rem 1rem; margin-bottom: .5rem;
             border-radius: 12px; border: 1px solid rgba(128,128,128,.25);}
      .step .icon {font-size: 1.4rem;}
      .step .name {font-weight: 600;}
      .step .desc {font-size: .82rem; opacity: .7;}
      .step .tag {margin-left: auto; font-size: .78rem; font-weight: 600; padding: .15rem .6rem;
                  border-radius: 999px; background: rgba(128,128,128,.15);}
      .step.running {border-color: #7c3aed; background: rgba(124,58,237,.08);}
      .step.running .tag {background: #7c3aed; color: #fff;}
      .step.done {border-color: rgba(34,197,94,.5); background: rgba(34,197,94,.07);}
      .step.done .tag {background: #22c55e; color: #fff;}
      .step.error {border-color: #ef4444; background: rgba(239,68,68,.08);}
      .step.error .tag {background: #ef4444; color: #fff;}
      #MainMenu, footer {visibility: hidden;}
    </style>
    <div class="hero">
      <h1>🔎 Research Studio</h1>
      <p>A multi-agent pipeline that searches, reads, writes and critiques — end to end.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

ss = st.session_state
ss.setdefault("history", [])  # list of run dicts, newest first
ss.setdefault("selected", None)
ss.setdefault("topic_input", "")


def render_steps(slot, status, times):
    html = ""
    for i, (icon, name, desc) in enumerate(STEPS):
        s = status[i]
        label = {"pending": "Waiting", "running": "Running…", "done": f"{times[i]:.1f}s", "error": "Failed"}[s]
        html += (
            f'<div class="step {s}"><span class="icon">{icon}</span>'
            f'<div><div class="name">{i + 1}. {name}</div><div class="desc">{desc}</div></div>'
            f'<span class="tag">{label}</span></div>'
        )
    slot.markdown(html, unsafe_allow_html=True)


# ---------- Sidebar ----------
with st.sidebar:
    st.header("History")
    if not ss.history:
        st.caption("Completed runs will appear here.")
    for idx, run in enumerate(ss.history):
        if st.button(f"{run['topic'][:36]}\n{run['time']} · {run['elapsed']:.0f}s",
                     key=f"hist_{idx}", use_container_width=True):
            ss.selected = idx
    if ss.history and st.button("Clear history", use_container_width=True):
        ss.history, ss.selected = [], None
        st.rerun()
    st.divider()
    st.caption("Tip: runs call live search and LLM APIs, so they can take a minute or two.")

# ---------- Input ----------
st.subheader("What do you want to research?")
cols = st.columns(len(EXAMPLES))
for col, ex in zip(cols, EXAMPLES):
    if col.button(ex, key=f"ex_{ex}", use_container_width=True):
        ss.topic_input = ex

with st.form("run_form", border=False):
    c1, c2 = st.columns([5, 1], vertical_alignment="bottom")
    topic = c1.text_input("Topic", key="topic_input", placeholder="Enter a topic…",
                          label_visibility="collapsed")
    submitted = c2.form_submit_button("Run ▶", type="primary", use_container_width=True)

# ---------- Run ----------
if submitted and topic.strip():
    topic = topic.strip()
    status = ["pending"] * len(STEPS)
    times = [0.0] * len(STEPS)
    starts = [0.0] * len(STEPS)
    st.markdown("#### Pipeline progress")
    slot = st.empty()
    render_steps(slot, status, times)
    bar = st.progress(0.0)
    logs = io.StringIO()
    t0 = time.time()

    def on_step(i, event, _state):
        if event == "start":
            status[i], starts[i] = "running", time.time()
        else:
            status[i], times[i] = "done", time.time() - starts[i]
        bar.progress(sum(s == "done" for s in status) / len(STEPS))
        render_steps(slot, status, times)

    try:
        with contextlib.redirect_stdout(logs):
            result = run_research_pipeline(topic, on_step=on_step)
        ss.history.insert(0, {
            "topic": topic, "state": result, "logs": logs.getvalue(),
            "elapsed": time.time() - t0, "times": times[:],
            "time": datetime.now().strftime("%H:%M"),
        })
        ss.selected = 0
        st.toast("Research complete", icon="✅")
        st.rerun()
    except Exception:
        for i, s in enumerate(status):
            if s == "running":
                status[i] = "error"
        render_steps(slot, status, times)
        st.error("The pipeline failed.")
        with st.expander("Error details"):
            st.code(traceback.format_exc())
        if logs.getvalue():
            with st.expander("Logs"):
                st.code(logs.getvalue(), language="text")

# ---------- Results ----------
if ss.selected is not None and ss.selected < len(ss.history):
    run = ss.history[ss.selected]
    state = run["state"]
    report = str(state["report"])
    st.divider()
    st.subheader(run["topic"])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total time", f"{run['elapsed']:.0f}s")
    m2.metric("Report words", f"{len(report.split()):,}")
    m3.metric("Slowest step", STEPS[run["times"].index(max(run["times"]))][1])
    m4.metric("Run at", run["time"])

    tab_report, tab_feedback, tab_sources, tab_logs = st.tabs(
        ["📝 Report", "🧐 Critic feedback", "🔗 Sources", "🖥️ Logs"])
    with tab_report:
        st.markdown(report)
        d1, d2 = st.columns(2)
        d1.download_button("⬇ Download report (.md)", report, file_name="report.md",
                           use_container_width=True)
        d2.download_button("⬇ Download with critique (.md)",
                           f"{report}\n\n---\n\n## Critic feedback\n\n{state['feedback']}",
                           file_name="report_with_critique.md", use_container_width=True)
    with tab_feedback:
        st.markdown(str(state["feedback"]))
    with tab_sources:
        with st.expander("Scraped content", expanded=True):
            st.markdown(str(state["scraped_content"]))
        with st.expander("Raw search results"):
            msgs = state["search_results"].get("messages", [])
            st.markdown(str(msgs[-1].content) if msgs else str(state["search_results"]))
    with tab_logs:
        st.code(run["logs"] or "(no output)", language="text")
