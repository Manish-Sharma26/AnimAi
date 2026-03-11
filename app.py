import streamlit as st
import os
import time
from agent.orchestrator import run_agent
from agent.feedback import save_good_example, get_feedback_stats

st.set_page_config(page_title="AnimAI Studio", page_icon="🎬", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #0F0F1A; }
    .main-title {
        font-size: 3.2rem; font-weight: 800;
        background: linear-gradient(90deg, #4FACFE, #00F2FE);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 0;
    }
    .subtitle { text-align: center; color: #888; font-size: 1.1rem; margin-bottom: 2rem; }
    .stTextArea textarea {
        background-color: #1A1A2E !important; color: white !important;
        border: 1px solid #4FACFE !important; border-radius: 10px !important;
    }
    .stButton > button {
        background: linear-gradient(90deg, #4FACFE, #00F2FE);
        color: #0F0F1A; font-weight: 700; border: none;
        border-radius: 10px; width: 100%;
    }
    .plan-box {
        background: #1A1A2E; border: 1px solid #4FACFE;
        border-radius: 10px; padding: 1rem; margin: 0.5rem 0;
    }
    .step-item { color: white; padding: 0.3rem 0; border-bottom: 1px solid #2A2A3E; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">🎬 AnimAI Studio</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-powered educational animations for every teacher</p>', unsafe_allow_html=True)

# Show feedback stats if any
stats = get_feedback_stats()
if stats["total"] > 0:
    st.info(f"🧠 System has learned from {stats['total']} approved animations")

st.divider()

# ── Example prompts ───────────────────────────────────────────────────────────
st.markdown("**💡 Try these examples:**")
examples = [
    "Animate bubble sort with array 5 2 8 1 9",
    "Show binary search on sorted array 1 3 5 7 9 11",
    "Visualize quadratic function parabola",
    "Demonstrate projectile motion",
    "Explain how vaccines work",
]

cols = st.columns(len(examples))
for i, example in enumerate(examples):
    with cols[i]:
        short = example[:15] + "..."
        if st.button(short, key=f"ex_{i}", help=example):
            st.session_state["prompt"] = example

# ── Input ─────────────────────────────────────────────────────────────────────
st.markdown("### 📝 Describe your animation")
prompt = st.text_area(
    label="prompt", label_visibility="collapsed",
    placeholder="e.g. Explain how binary search works on a sorted array of 8 elements...",
    height=120,
    value=st.session_state.get("prompt", ""),
    key="prompt_input"
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    generate_btn = st.button("🚀 Generate Animation", disabled=not prompt)

# ── Generation ────────────────────────────────────────────────────────────────
if generate_btn and prompt:
    st.divider()
    st.markdown("### ⚙️ Generating your animation...")

    # Live progress steps
    p_plan    = st.empty()
    p_code    = st.empty()
    p_compile = st.empty()
    p_audio   = st.empty()

    def show_step(placeholder, icon, text, color="#4FACFE"):
        placeholder.markdown(
            f'<div style="background:#1A1A2E; border-left:3px solid {color}; '
            f'padding:0.6rem 1rem; margin:0.3rem 0; border-radius:0 8px 8px 0; color:white">'
            f'{icon} {text}</div>', unsafe_allow_html=True)

    show_step(p_plan,    "⏳", "Planning animation structure...", "#F9CA24")
    show_step(p_code,    "⬜", "Generating Manim code...", "#444")
    show_step(p_compile, "⬜", "Compiling animation...", "#444")
    show_step(p_audio,   "⬜", "Adding voice narration...", "#444")

    try:
        result = run_agent(prompt)

        # Update steps based on result
        show_step(p_plan,    "✅", "Animation planned!", "#6AB04C")
        show_step(p_code,    "✅", f"Code generated ({result.get('attempts', 1)} attempt(s))", "#6AB04C")
        show_step(p_compile, "✅", "Compilation successful!", "#6AB04C")
        show_step(p_audio,
                  "✅" if result.get("has_audio") else "⚠️",
                  "Voice narration added!" if result.get("has_audio") else "Silent video (no internet for TTS)",
                  "#6AB04C" if result.get("has_audio") else "#F9CA24")

        st.divider()

        if result["status"] == "success":

            # Show plan that was used
            plan = result.get("plan", {})
            if plan:
                with st.expander("🧠 Animation Plan (what AI decided to create)"):
                    st.markdown(f'<div class="plan-box">', unsafe_allow_html=True)
                    st.markdown(f"**Title:** {plan.get('title', '')}")
                    st.markdown(f"**Visual Style:** {plan.get('visual_style', '')}")
                    st.markdown(f"**Planned Duration:** {plan.get('duration_seconds', 45)}s")
                    st.markdown("**Steps:**")
                    for i, step in enumerate(plan.get("steps", []), 1):
                        st.markdown(f"&nbsp;&nbsp;{i}. {step}")
                    st.markdown(f'</div>', unsafe_allow_html=True)

            # Video player
            video_path = result["video_path"]
            if os.path.exists(video_path):
                with open(video_path, "rb") as f:
                    video_bytes = f.read()

                st.success("✅ Your animation is ready!")
                st.video(video_bytes)

                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button("⬇️ Download MP4", video_bytes,
                                       "animation.mp4", "video/mp4",
                                       use_container_width=True)
                with col2:
                    if st.button("🔄 Regenerate", use_container_width=True):
                        st.rerun()
                with col3:
                    if st.button("🆕 New Animation", use_container_width=True):
                        st.session_state["prompt"] = ""
                        st.rerun()

                # Feedback section
                st.divider()
                st.markdown("### Was this animation good?")
                st.markdown("Your feedback helps the AI improve over time.")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👍 Yes, this is great!", use_container_width=True):
                        save_good_example(
                            query=prompt,
                            code=result.get("code", ""),
                            category=result.get("category", "diagram"),
                            plan=result.get("plan")
                        )
                        st.success("🎉 Thank you! This animation has been saved to improve future generations.")

                with col2:
                    if st.button("👎 No, needs improvement", use_container_width=True):
                        st.info("Thanks for the feedback. Try rephrasing your prompt for better results.")
                        with st.expander("💡 Tips for better prompts"):
                            st.markdown("""
                            - Be specific: *"bubble sort with array [5,2,8,1]"* not *"sorting"*
                            - Mention the topic clearly: *"explain photosynthesis step by step"*
                            - For math: *"show graph of y = x squared"*
                            - For physics: *"demonstrate projectile motion at 45 degrees"*
                            """)

                # Code expander
                with st.expander("👨‍💻 View Generated Code"):
                    st.code(result.get("code", ""), language="python")

                # Voiceover script
                if result.get("has_audio"):
                    import re
                    voiceover_lines = re.findall(r'#\s*VOICEOVER:\s*(.+)', result.get("code", ""))
                    if voiceover_lines:
                        with st.expander("🎙️ Voiceover Script"):
                            for i, line in enumerate(voiceover_lines, 1):
                                st.write(f"**{i}.** {line}")

        else:
            st.error("❌ Could not generate animation after multiple attempts.")
            st.info("💡 Try rephrasing your prompt with more specific details.")
            with st.expander("🔍 Error Details"):
                st.code(result.get("error", "Unknown error")[:500])

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        with st.expander("Details"):
            st.code(traceback.format_exc())

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center; color:#444; font-size:0.85rem;'>
    AnimAI Studio — Powered by Llama-3 70B + Manim Community Edition<br>
    Multi-agent AI system: Planner → Coder → Debugger → Voice
</div>
""", unsafe_allow_html=True)