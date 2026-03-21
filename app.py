import streamlit as st
import os
import json
from agent.orchestrator import build_plan, run_agent_with_plan, apply_user_changes
from agent.planner import normalize_plan
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

if "draft_plan" not in st.session_state:
    st.session_state["draft_plan"] = None
if "approved_plan" not in st.session_state:
    st.session_state["approved_plan"] = None
if "plan_prompt" not in st.session_state:
    st.session_state["plan_prompt"] = ""
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None
if "last_query" not in st.session_state:
    st.session_state["last_query"] = ""
if "last_plan" not in st.session_state:
    st.session_state["last_plan"] = None

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
    plan_btn = st.button("🧠 Generate Plan", disabled=not prompt)

# Reset stale plans when prompt changes
if prompt and st.session_state.get("plan_prompt") and prompt != st.session_state.get("plan_prompt"):
    st.session_state["draft_plan"] = None
    st.session_state["approved_plan"] = None

if plan_btn and prompt:
    with st.spinner("🧑‍🏫 Teacher is explaining the concept, then building your animation plan..."):
        draft_plan = build_plan(prompt)
    st.session_state["draft_plan"] = draft_plan
    st.session_state["approved_plan"] = None
    st.session_state["plan_prompt"] = prompt

# ── Plan Approval ────────────────────────────────────────────────────────────
if st.session_state.get("draft_plan"):
    st.divider()
    st.markdown("### 🧠 Review the plan before generation")

    draft_plan = st.session_state["draft_plan"]

    # Show Teacher Explanation if available
    teacher_exp = draft_plan.get("teacher_explanation", {})
    if teacher_exp:
        with st.expander("🧑‍🏫 Teacher's Concept Explanation", expanded=True):
            st.markdown(f"**Core Idea:** {teacher_exp.get('core_idea', '')}")
            key_terms = teacher_exp.get("key_terms", [])
            if key_terms:
                terms_md = ", ".join(f"**{t.get('term', '')}** ({t.get('meaning', '')})" for t in key_terms)
                st.markdown(f"**Key Terms:** {terms_md}")
            steps_list = teacher_exp.get("step_by_step", [])
            if steps_list:
                st.markdown("**Step-by-Step:**")
                for i, s in enumerate(steps_list, 1):
                    st.markdown(f"&nbsp;&nbsp;{i}. {s}")
            analogy = teacher_exp.get("analogy", "")
            if analogy:
                st.markdown(f"💡 **Analogy:** {analogy}")
            misconception = teacher_exp.get("misconception", "")
            if misconception:
                st.markdown(f"⚠️ **Common Misconception:** {misconception}")
            takeaway = teacher_exp.get("takeaway", "")
            if takeaway:
                st.markdown(f"🎯 **Takeaway:** {takeaway}")

    st.markdown('<div class="plan-box">', unsafe_allow_html=True)
    st.markdown(f"**Title:** {draft_plan.get('title', '')}")
    st.markdown(f"**Visual Style:** {draft_plan.get('visual_style', '')}")
    st.markdown(f"**Estimated Duration:** {draft_plan.get('duration_seconds', 45)} seconds")
    st.markdown(f"**Opening Scene:** {draft_plan.get('opening_scene', '')}")
    st.markdown("**Steps:**")
    for i, step in enumerate(draft_plan.get("steps", []), 1):
        st.markdown(f"&nbsp;&nbsp;{i}. {step}")

    full_script = draft_plan.get("full_script", [])
    if full_script:
        st.markdown("**Full Start-to-End Script:**")
        for i, beat in enumerate(full_script, 1):
            st.markdown(f"&nbsp;&nbsp;{i}. {beat}")

    st.markdown(f"**Closing Scene:** {draft_plan.get('closing_scene', '')}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("#### ✏️ Edit the plan (JSON)")
    st.caption("You can edit opening_scene, steps, voiceovers, full_script, and duration_seconds before generation.")

    editable_json = st.text_area(
        "Editable Plan JSON",
        value=json.dumps(draft_plan, indent=2),
        height=320,
        key="editable_plan_json"
    )

    c1, c2 = st.columns(2)
    with c1:
        approve_btn = st.button("✅ Use This Plan", use_container_width=True)
    with c2:
        regen_plan_btn = st.button("🔄 Regenerate Plan", use_container_width=True)

    if regen_plan_btn and prompt:
        with st.spinner("Regenerating plan from prompt..."):
            refreshed = build_plan(prompt)
        st.session_state["draft_plan"] = refreshed
        st.session_state["approved_plan"] = None
        st.rerun()

    if approve_btn:
        try:
            parsed = json.loads(editable_json)
            approved = normalize_plan(parsed, prompt)
            st.session_state["approved_plan"] = approved
            st.success("Plan approved. You can generate the final narrated animation now.")
        except Exception as e:
            st.error(f"Plan JSON is invalid: {e}")

if st.session_state.get("approved_plan"):
    st.markdown("### 🚀 Generate final video")
    generate_btn = st.button("🎬 Generate Video With Voice", use_container_width=True)
else:
    generate_btn = False

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
    show_step(p_audio,   "⬜", "Rendering voiceover in Manim...", "#444")

    try:
        approved_plan = st.session_state.get("approved_plan")
        result = run_agent_with_plan(prompt, approved_plan)
        st.session_state["last_result"] = result
        st.session_state["last_query"] = prompt
        st.session_state["last_plan"] = approved_plan

        # Update steps based on result
        show_step(p_plan,    "✅", "Animation planned!", "#6AB04C")
        show_step(p_code,    "✅", f"Code generated ({result.get('attempts', 1)} attempt(s))", "#6AB04C")
        show_step(p_compile, "✅", "Compilation successful!", "#6AB04C")
        show_step(p_audio,
                  "✅" if result.get("has_audio") else "⚠️",
                  "Voice narration rendered!" if result.get("has_audio") else "Video generated, but no voiceover blocks were detected.",
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
                    st.markdown(f"**Opening Scene:** {plan.get('opening_scene', '')}")
                    st.markdown("**Steps:**")
                    for i, step in enumerate(plan.get("steps", []), 1):
                        st.markdown(f"&nbsp;&nbsp;{i}. {step}")

                    full_script = plan.get("full_script", [])
                    if full_script:
                        st.markdown("**Full Script:**")
                        for i, beat in enumerate(full_script, 1):
                            st.markdown(f"&nbsp;&nbsp;{i}. {beat}")

                    st.markdown(f"**Closing Scene:** {plan.get('closing_scene', '')}")
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
                        st.session_state["draft_plan"] = None
                        st.session_state["approved_plan"] = None
                        st.session_state["plan_prompt"] = ""
                        st.session_state["last_result"] = None
                        st.session_state["last_query"] = ""
                        st.session_state["last_plan"] = None
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

# ── Post-Generation Revision Loop ─────────────────────────────────────────────
last_result = st.session_state.get("last_result") or {}
if last_result.get("status") == "success":
    st.divider()
    st.markdown("### ✏️ Suggest changes to this video")
    st.caption("Describe what to change; AnimAI will revise existing code and retry rendering up to 3 times.")

    change_request = st.text_area(
        "What should be changed?",
        placeholder="e.g. Make the full binary tree visible, reduce label overlap, and slow down traversal narration.",
        height=110,
        key="change_request_input",
    )

    apply_changes_btn = st.button(
        "♻️ Apply Changes (max 3 tries)",
        use_container_width=True,
        disabled=not change_request.strip(),
    )

    if apply_changes_btn:
        with st.spinner("Applying requested changes and regenerating video..."):
            revised = apply_user_changes(
                user_query=st.session_state.get("last_query", prompt),
                approved_plan=st.session_state.get("last_plan") or last_result.get("plan", {}),
                existing_code=last_result.get("code", ""),
                change_request=change_request.strip(),
            )

        if revised.get("status") == "success":
            st.session_state["last_result"] = revised
            st.session_state["last_plan"] = revised.get("plan") or st.session_state.get("last_plan")
            st.success("✅ Changes applied successfully. Updated video is ready below.")

            revised_path = revised.get("video_path", "")
            if revised_path and os.path.exists(revised_path):
                with open(revised_path, "rb") as f:
                    revised_video = f.read()
                st.video(revised_video)
                st.download_button(
                    "⬇️ Download Updated MP4",
                    revised_video,
                    "animation_updated.mp4",
                    "video/mp4",
                    use_container_width=True,
                )
        else:
            st.error("❌ Could not apply changes after 3 revision tries.")
            with st.expander("🔍 Revision Error Details"):
                st.code((revised.get("error") or "Unknown error")[:1200])

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center; color:#444; font-size:0.85rem;'>
    AnimAI Studio — Powered by Llama-3 70B + Manim Community Edition<br>
    Multi-agent AI system: Planner → Coder → Debugger → Voice
</div>
""", unsafe_allow_html=True)