"""
Run this ONCE to download Manim docs and build the search index.
After running, you'll have:
  - rag/manim_chunks.json   (all doc chunks)
  - rag/manim_docs.index    (FAISS search index)
"""

import requests
import json
import os
import re

# Key Manim documentation pages to download
MANIM_DOC_URLS = [
    # Core Manim source docs
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/geometry/arc.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/geometry/polygram.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/geometry/line.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/text/text_mobject.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/types/vectorized_mobject.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/animation/creation.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/animation/transform.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/animation/indication.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/animation/movement.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/graph.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/table.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/graphing/coordinate_systems.py",
    # Manim-Voiceover source docs — FULL LIBRARY
    "https://raw.githubusercontent.com/ManimCommunity/manim-voiceover/main/src/manim_voiceover/voiceover_scene.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim-voiceover/main/src/manim_voiceover/services/gtts.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim-voiceover/main/src/manim_voiceover/tracker.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim-voiceover/main/src/manim_voiceover/helper.py",
    # Manim-Voiceover examples — Only the safe non-bookmark examples
    "https://raw.githubusercontent.com/ManimCommunity/manim-voiceover/main/examples/gtts-example.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim-voiceover/main/examples/approximating-tau.py",
    # Manim animation fading/composition
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/animation/fading.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/animation/composition.py",
    # Math / LaTeX text rendering
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/text/tex_mobject.py",
    # Shape matchers (SurroundingRectangle, BackgroundRectangle, Underline)
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/geometry/shape_matchers.py",
    # Growing animations (GrowFromCenter, GrowArrow, GrowFromEdge, etc.)
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/animation/growing.py",
    # Rotation animation
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/animation/rotation.py",
    # ValueTracker for dynamic animations with updaters
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/value_tracker.py",
    # Matrix visualization (Matrix, DecimalMatrix, IntegerMatrix)
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/matrix.py",
    # NumberLine (used in probability, statistics, timelines)
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/graphing/number_line.py",
    # Brace and BraceBetweenPoints
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/svg/brace.py",
    # Speed modifier (ChangeSpeed)
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/animation/speedmodifier.py",
    # Arrow tips (ArrowTip, ArrowTriangleTip, etc.)
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/geometry/tips.py",
    # Updaters (UpdateFromFunc, UpdateFromAlphaFunc, always_redraw)
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/animation/updaters/update.py",
    # ParametricFunction, FunctionGraph
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/graphing/functions.py",
]

# Also add handcrafted pattern examples for common animation types
HANDCRAFTED_PATTERNS = [
    # ────────────────────────────────────────────────────────────────
    # API REFERENCE: Text() valid parameters — prevent hallucinated params
    # ────────────────────────────────────────────────────────────────
    {
        "title": "Text() class — VALID parameters only (Manim v0.20.1)",
        "content": """
# MANIM API REFERENCE: Text() class (manim.mobject.text.text_mobject.Text)
# Source: Manim Community v0.20.1
#
# VALID constructor parameters:
#   Text(text, font='', font_size=DEFAULT_FONT_SIZE, color=WHITE,
#        fill_opacity=1, stroke_width=0, tab_width=4, line_spacing=-1,
#        disable_ligatures=False, warn_missing_font=True,
#        weight=NORMAL, slant=NORMAL, **kwargs)
#
# ❌ INVALID (NOT accepted by Text()) — these cause TypeError crashes:
#   alignment=  → does NOT exist on Text()
#   max_width=  → does NOT exist on Text()
#   justify=    → does NOT exist on Text()
#
# ✅ CORRECT alternatives:
#
# To align multiple text items left:
#   VGroup(t1, t2, t3).arrange(DOWN, aligned_edge=LEFT)
#
# To limit text width:
#   my_text = Text("Long text here", font_size=24)
#   my_text.scale_to_fit_width(config.frame_width * 0.8)
#
# For multi-line text with paragraph-level alignment:
#   Paragraph("Line 1", "Line 2", "Line 3", font_size=24, alignment="left")
#   NOTE: alignment= IS valid on Paragraph(), NOT on Text()
#
# EXAMPLES OF CORRECT Text() USAGE:
correct_text = Text("Hello World", font_size=36, color=WHITE, weight=BOLD)
correct_text2 = Text("Multi", font_size=28, color="#4FACFE", line_spacing=1.2)
labels = VGroup(
    Text("Step 1", font_size=22, color=WHITE),
    Text("Step 2", font_size=22, color=WHITE),
    Text("Step 3", font_size=22, color=WHITE),
).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
"""
    },
    {
        "title": "VoiceoverScene 3D constraint — set_camera_orientation is FORBIDDEN",
        "content": """
# CRITICAL API CONSTRAINT: VoiceoverScene vs ThreeDScene
#
# GeneratedScene extends VoiceoverScene.
# VoiceoverScene does NOT inherit from ThreeDScene.
#
# ❌ FORBIDDEN — these crash with AttributeError on VoiceoverScene:
#   self.set_camera_orientation(phi=75 * DEGREES, theta=30 * DEGREES)
#   ThreeDAxes(...)       → requires ThreeDScene
#   Surface(...)          → requires ThreeDScene
#   Sphere(...)           → requires ThreeDScene (use Circle for 2D alternative)
#
# ✅ CORRECT: Simulate 3D depth using 2D Axes and layered VGroups:
#
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class Correct3DVisualization(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService(lang="en"))
        self.camera.background_color = "#0F0F1A"

        # ✅ Use 2D Axes with Axes.plot() for function curves (gradient descent, etc.)
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[0, 6, 1],
            x_length=8,
            y_length=5,
            axis_config={"include_numbers": True},
        ).move_to(ORIGIN)
        labels = axes.get_axis_labels(x_label="x", y_label="Cost")

        # ✅ Plot a parabolic cost function (gradient descent visualization)
        cost_curve = axes.plot(lambda x: 0.5 * x**2 + 1, color="#4FACFE")
        ball = Dot(axes.c2p(2.5, 0.5 * 2.5**2 + 1), color=RED, radius=0.12)

        with self.voiceover(text="This curve shows the cost function.") as tracker:
            self.play(
                Create(axes), Create(labels), Create(cost_curve),
                FadeIn(ball), run_time=tracker.duration
            )
"""
    },
    {
        "title": "Voiceover timing with tracker.duration — NO bookmarks (GTTSService)",
        "content": """
# VOICEOVER TIMING REFERENCE: GTTSService with tracker.duration
#
# GTTSService does NOT support bookmarks. NEVER use:
#   <bookmark mark='name'/>   → CRASHES with 'Word boundaries required'
#   self.wait_until_bookmark()→ CRASHES with 'Word boundaries required'
#
# ✅ ALWAYS use tracker.duration and tracker.get_remaining_duration():
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class CorrectTimingExample(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService(lang="en"))
        self.camera.background_color = "#0F0F1A"

        # Pattern 1: Split total duration into fractions
        with self.voiceover(text="First we show X, then Y appears.") as tracker:
            x = Circle(color="#4FACFE").move_to(LEFT * 2)
            y = Square(color="#F9CA24").move_to(RIGHT * 2)
            self.play(Create(x), run_time=tracker.duration * 0.5)
            self.play(FadeIn(y), run_time=tracker.get_remaining_duration())

        # Pattern 2: Multiple sequential animations summing to duration
        with self.voiceover(text="Watch the transformation happen step by step.") as tracker:
            step1_time = tracker.duration * 0.4
            step2_time = tracker.duration * 0.4
            step3_time = tracker.get_remaining_duration()
            self.play(x.animate.set_fill("#4FACFE", opacity=0.8), run_time=step1_time)
            self.play(Transform(x, y), run_time=step2_time)
            self.play(FadeOut(x), run_time=step3_time)
"""
    },
    {
        "title": "Voiceover tracker duration pattern — animation timing control",
        "content": """
# Pattern: Using tracker.duration and tracker.get_remaining_duration()
# for fine-grained animation timing with voiceover
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class TrackerDurationExample(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService(lang="en"))
        self.camera.background_color = "#0F0F1A"

        # Use tracker.duration to match animation length to speech length
        with self.voiceover(text="Watch as this circle slowly grows larger.") as tracker:
            circle = Circle(radius=0.5, color="#4FACFE")
            self.play(Create(circle), run_time=tracker.duration * 0.4)
            self.play(circle.animate.scale(2.5), run_time=tracker.duration * 0.6)

        # Use get_remaining_duration() to fill remaining time
        with self.voiceover(text="Now it transforms into a square and changes color.") as tracker:
            square = Square(side_length=2.0, color="#F9CA24")
            self.play(Transform(circle, square), run_time=tracker.duration * 0.5)
            self.play(
                square.animate.set_fill("#6AB04C", opacity=0.8),
                run_time=tracker.get_remaining_duration()
            )

        self.wait(1.0)
"""
    },
    {
        "title": "VoiceoverScene with GTTSService pattern",
        "content": """
# Pattern: Using VoiceoverScene with GTTSService for narrated educational animations
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class NarratedExample(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService(lang="en"))
        self.camera.background_color = "#0F0F1A"

        title = Text("Example Topic", font_size=48, color="#4FACFE")
        title.to_edge(UP, buff=0.5)
        underline = Line(LEFT, RIGHT, color="#4FACFE").scale(0.5)
        underline.next_to(title, DOWN, buff=0.3)
        self.play(Write(title), Create(underline))

        # VOICEOVER: Introduction to the concept
        with self.voiceover(text="Welcome. Let us explore this concept step by step.") as tracker:
            intro = Text("Key Concept", font_size=36, color=WHITE)
            intro.next_to(title, DOWN, buff=1.0)
            self.play(FadeIn(intro))

        # VOICEOVER: Step 1 explanation
        with self.voiceover(text="First, we set up the main elements that we will work with.") as tracker:
            self.play(FadeOut(intro))
            self.wait(0.3)
            circle = Circle(radius=1.0, color="#4FACFE", stroke_width=3)
            circle.move_to(ORIGIN)
            label = Text("Element A", font_size=24, color=WHITE).next_to(circle, DOWN, buff=0.3)
            step1_group = VGroup(circle, label)
            self.play(Create(circle), FadeIn(label))

        # VOICEOVER: Step 2 — transform and highlight
        with self.voiceover(text="Now watch as the element transforms to show the result.") as tracker:
            self.play(circle.animate.set_fill("#6AB04C", opacity=0.8))
            result_label = Text("Result!", font_size=28, color="#6AB04C")
            result_label.next_to(circle, UP, buff=0.3)
            self.play(FadeIn(result_label))

        # VOICEOVER: Closing summary
        with self.voiceover(text="And that is how this concept works in practice.") as tracker:
            self.play(FadeOut(step1_group), FadeOut(result_label))
            self.wait(0.3)
            banner = RoundedRectangle(corner_radius=0.2, width=6, height=1.2)
            banner.set_fill("#0A2A0A", opacity=1).set_stroke("#6AB04C", width=3)
            banner_text = Text("Concept Complete!", font_size=36, color="#6AB04C", weight=BOLD)
            banner_text.move_to(banner)
            self.play(FadeIn(VGroup(banner, banner_text), scale=1.2))
            self.wait(2.0)
"""
    },
    # ────────────────────────────────────────────────────────────────
    # COMPLETE 5-SEGMENT VIDEO TEMPLATE (the most critical pattern)
    # ────────────────────────────────────────────────────────────────
    {
        "title": "Complete 5-segment educational video pattern — intro, theory, animation, user message, summary",
        "content": """
# Pattern: Complete 5-segment educational video structure
# SEGMENT 1: Introduction (title + hook)
# SEGMENT 2: Theory & Analogy (text explanation)
# SEGMENT 3: Core Animation (visual demonstration)
# SEGMENT 4: User's Message (echo query + answer)
# SEGMENT 5: Summary & Takeaway (closing banner)
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class FiveSegmentVideo(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService(lang="en"))
        self.camera.background_color = "#0F0F1A"

        # ═══ SEGMENT 1: INTRODUCTION ═══
        title = Text("Understanding the Concept", font_size=44, color="#4FACFE", weight=BOLD)
        title.to_edge(UP, buff=0.5)
        underline = Line(LEFT * 3, RIGHT * 3, color="#4FACFE", stroke_width=2)
        underline.next_to(title, DOWN, buff=0.2)

        with self.voiceover(text="Have you ever wondered how this works? Let us find out together.") as tracker:
            self.play(Write(title), Create(underline))
            hook = Text("Why does this matter?", font_size=30, color="#F9CA24")
            hook.move_to(ORIGIN)
            self.play(FadeIn(hook, shift=UP * 0.3))

        # ═══ FULL CLEANUP between segments ═══
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(0.3)

        # ═══ SEGMENT 2: THEORY & ANALOGY ═══
        with self.voiceover(text="Think of it like a ball rolling downhill. It always moves toward the lowest point.") as tracker:
            # Theory text on left side
            theory_title = Text("The Key Idea", font_size=32, color="#4FACFE", weight=BOLD)
            theory_title.to_edge(UP, buff=0.5)
            theory_text = Text("The system finds the\\nbest solution step by step", font_size=22, color=WHITE)
            theory_text.next_to(theory_title, DOWN, buff=0.8)
            theory_group = VGroup(theory_title, theory_text)
            theory_group.to_edge(LEFT, buff=1.0)

            # Analogy visual on right
            analogy_label = Text("Like a ball\\nrolling downhill", font_size=20, color="#F9CA24")
            analogy_label.to_edge(RIGHT, buff=1.2).shift(UP * 0.5)

            self.play(FadeIn(theory_group), FadeIn(analogy_label))

        # ═══ FULL CLEANUP between segments ═══
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(0.3)

        # ═══ SEGMENT 3: CORE ANIMATION ═══
        with self.voiceover(text="Now let us see this in action. Watch how the value changes over time.") as tracker:
            axes = Axes(x_range=[0, 5, 1], y_range=[0, 10, 2],
                       axis_config={"color": "#4FACFE", "stroke_width": 2})
            axes.scale(0.7).to_edge(LEFT, buff=1.0)
            curve = axes.plot(lambda x: (x - 2.5)**2 + 1, color="#F9CA24", stroke_width=3)
            key_text = Text("Value decreases!", font_size=24, color=YELLOW)
            key_text.to_edge(RIGHT, buff=0.8).shift(UP * 0.5)
            self.play(Create(axes), run_time=0.8)
            self.play(Create(curve), FadeIn(key_text), run_time=1.5)

            dot = Dot(axes.c2p(0.5, (0.5 - 2.5)**2 + 1), color="#6AB04C", radius=0.12)
            self.play(FadeIn(dot))
            self.play(dot.animate.move_to(axes.c2p(2.5, 1)), run_time=2.0)

        # ═══ FULL CLEANUP between segments ═══
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(0.3)

        # ═══ SEGMENT 4: USER'S MESSAGE ═══
        with self.voiceover(text="So to answer your question: the system optimizes by taking small steps toward the best answer.") as tracker:
            answer_label = Text("Your Question, Answered", font_size=32, color="#4FACFE", weight=BOLD)
            answer_label.to_edge(UP, buff=0.8)
            answer_text = Text("It works by taking small,\\nrepeated improvements", font_size=26, color=WHITE)
            answer_text.move_to(ORIGIN)
            self.play(FadeIn(answer_label, shift=DOWN * 0.3))
            self.play(FadeIn(answer_text))

        # ═══ FULL CLEANUP between segments ═══
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(0.3)

        # ═══ SEGMENT 5: SUMMARY & TAKEAWAY ═══
        with self.voiceover(text="Remember: small steps lead to the best solution. That is the key takeaway.") as tracker:
            banner = RoundedRectangle(corner_radius=0.25, width=10, height=1.5)
            banner.set_fill("#0A2A0A", opacity=1).set_stroke("#6AB04C", width=3)
            banner_text = Text("Key Takeaway: Small Steps → Best Solution", font_size=28, color="#6AB04C", weight=BOLD)
            banner_text.move_to(banner)
            self.play(FadeIn(VGroup(banner, banner_text), scale=1.1))

        self.wait(2.0)
"""
    },
    # ────────────────────────────────────────────────────────────────
    # SCENE CLEANUP BETWEEN STEPS (anti-overlap pattern)
    # ────────────────────────────────────────────────────────────────
    {
        "title": "Scene cleanup pattern — preventing element pile-up between steps",
        "content": """
# Pattern: Proper cleanup between animation steps to prevent overlap
# CRITICAL: Every step must clean up previous elements before adding new ones
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class CleanupExample(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService(lang="en"))
        self.camera.background_color = "#0F0F1A"

        # --- Step 1 ---
        step1_visual = Circle(radius=1.0, color="#4FACFE")
        step1_text = Text("Step 1", font_size=28, color=WHITE).next_to(step1_visual, DOWN)
        step1_key = Text("First concept", font_size=24, color=YELLOW).to_edge(RIGHT, buff=0.8)
        step1_group = VGroup(step1_visual, step1_text, step1_key)

        with self.voiceover(text="Here is the first concept.") as tracker:
            self.play(FadeIn(step1_group))

        # --- Step 2: CLEANUP step 1, then show step 2 ---
        self.play(FadeOut(step1_group))  # MANDATORY CLEANUP
        self.wait(0.3)                   # Breathing room

        step2_visual = Square(side_length=1.5, color="#F9CA24")
        step2_text = Text("Step 2", font_size=28, color=WHITE).next_to(step2_visual, DOWN)
        step2_key = Text("Second concept", font_size=24, color=YELLOW).to_edge(RIGHT, buff=0.8)
        step2_group = VGroup(step2_visual, step2_text, step2_key)

        with self.voiceover(text="Now the second concept replaces the first.") as tracker:
            self.play(FadeIn(step2_group))

        # --- Step 3: FULL SCREEN CLEAR for major transition ---
        self.play(*[FadeOut(mob) for mob in self.mobjects])  # Clear EVERYTHING
        self.wait(0.3)

        step3_visual = Triangle(color="#6AB04C").scale(1.5)
        step3_text = Text("Final Result", font_size=28, color=WHITE).next_to(step3_visual, DOWN)
        step3_group = VGroup(step3_visual, step3_text)

        with self.voiceover(text="And here is the final result.") as tracker:
            self.play(FadeIn(step3_group, scale=1.2))

        self.wait(1.0)
"""
    },
    # ────────────────────────────────────────────────────────────────
    # SPLIT-SCREEN LAYOUT PATTERN
    # ────────────────────────────────────────────────────────────────
    {
        "title": "Split-screen layout pattern — visual left, key text right",
        "content": """
# Pattern: Split-screen layout with main visual on LEFT and key text on RIGHT
# LEFT ~60% of screen (x = [-6.5, 1.5]) for visuals
# RIGHT ~35% of screen (x = [2.5, 6.5]) for key text panel
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class SplitScreenExample(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService(lang="en"))
        self.camera.background_color = "#0F0F1A"

        # Main visual — LEFT side
        axes = Axes(x_range=[0, 5, 1], y_range=[0, 8, 2],
                   axis_config={"color": "#4FACFE", "stroke_width": 2})
        axes.scale(0.6)
        axes.to_edge(LEFT, buff=0.8).shift(DOWN * 0.3)  # Left 60%

        # Key text panel — RIGHT side
        key_text_bg = RoundedRectangle(corner_radius=0.15, width=3.5, height=1.2)
        key_text_bg.set_fill("#1A1A2E", opacity=0.8).set_stroke("#F9CA24", width=1)
        key_text_bg.to_edge(RIGHT, buff=0.5).shift(UP * 0.5)
        key_label = Text("Cost = How Wrong\\nWe Are", font_size=22, color=YELLOW)
        key_label.move_to(key_text_bg)
        key_panel = VGroup(key_text_bg, key_label)

        with self.voiceover(text="The cost function measures how wrong our prediction is.") as tracker:
            self.play(Create(axes))
            curve = axes.plot(lambda x: (x - 2.5)**2 + 1, color="#F9CA24")
            self.play(Create(curve), FadeIn(key_panel))

        # Clean up key panel, swap for next key text
        new_key_label = Text("Gradient → Direction\\nof Steepest Descent", font_size=22, color=YELLOW)
        new_key_bg = RoundedRectangle(corner_radius=0.15, width=3.5, height=1.2)
        new_key_bg.set_fill("#1A1A2E", opacity=0.8).set_stroke("#F9CA24", width=1)
        new_key_bg.to_edge(RIGHT, buff=0.5).shift(UP * 0.5)
        new_key_label.move_to(new_key_bg)
        new_key_panel = VGroup(new_key_bg, new_key_label)

        with self.voiceover(text="The gradient tells us which direction to move to reduce cost.") as tracker:
            self.play(FadeOut(key_panel), FadeIn(new_key_panel))
            # Add gradient arrow on the curve
            arrow = Arrow(
                axes.c2p(1, (1-2.5)**2+1),
                axes.c2p(2, (2-2.5)**2+1),
                color="#6AB04C", stroke_width=3
            )
            self.play(Create(arrow), run_time=0.8)

        self.wait(1.0)
"""
    },
    # ────────────────────────────────────────────────────────────────
    # ML: GRADIENT DESCENT COMPLETE ANIMATION
    # ────────────────────────────────────────────────────────────────
    {
        "title": "ML gradient descent animation pattern — complete working example",
        "content": """
# Pattern: Gradient descent with cost curve, moving dot, and learning rate
# This is a COMPLETE WORKING EXAMPLE for ML animation
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class GradientDescentExample(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService(lang="en"))
        self.camera.background_color = "#0F0F1A"

        # ═══ SEGMENT 1: INTRODUCTION ═══
        title = Text("Gradient Descent", font_size=44, color="#4FACFE", weight=BOLD)
        title.to_edge(UP, buff=0.5)
        underline = Line(LEFT * 2.5, RIGHT * 2.5, color="#4FACFE")
        underline.next_to(title, DOWN, buff=0.2)

        with self.voiceover(text="How does a machine learn from its mistakes? That is what gradient descent is all about.") as tracker:
            self.play(Write(title), Create(underline))
            hook = Text("How does AI improve?", font_size=28, color="#F9CA24")
            hook.move_to(ORIGIN)
            self.play(FadeIn(hook, shift=UP * 0.3))

        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(0.3)

        # ═══ SEGMENT 2: THEORY ═══
        with self.voiceover(text="Imagine a ball on a hilly landscape. It naturally rolls to the lowest valley. Gradient descent works the same way for AI.") as tracker:
            theory = Text("Core Idea:", font_size=28, color="#4FACFE", weight=BOLD)
            theory.to_edge(UP, buff=0.6).to_edge(LEFT, buff=1.0)
            explanation = Text("Find the lowest point\\non the error surface", font_size=22, color=WHITE)
            explanation.next_to(theory, DOWN, buff=0.5, aligned_edge=LEFT)
            analogy = Text("Like a ball rolling\\nto the valley floor", font_size=20, color="#F9CA24")
            analogy.to_edge(RIGHT, buff=1.0).shift(UP * 0.5)
            self.play(FadeIn(theory), FadeIn(explanation), FadeIn(analogy))

        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(0.3)

        # ═══ SEGMENT 3: CORE ANIMATION ═══
        axes = Axes(
            x_range=[-3, 3, 1], y_range=[0, 10, 2],
            axis_config={"color": "#4FACFE", "stroke_width": 2},
            tips=False
        ).scale(0.65).to_edge(LEFT, buff=0.8).shift(DOWN * 0.2)

        x_label = Text("Parameter", font_size=18, color="#4FACFE").next_to(axes, DOWN, buff=0.3)
        y_label = Text("Cost", font_size=18, color="#4FACFE").next_to(axes, LEFT, buff=0.3)
        cost_curve = axes.plot(lambda x: x**2 + 1, color="#F9CA24", stroke_width=3)

        key_panel = Text("Cost = How Wrong\\nThe Model Is", font_size=22, color=YELLOW)
        key_panel.to_edge(RIGHT, buff=0.8).shift(UP * 1.0)

        with self.voiceover(text="This curve shows the cost, or how wrong our model is. We want to reach the bottom, the minimum cost.") as tracker:
            self.play(Create(axes), FadeIn(x_label), FadeIn(y_label))
            self.play(Create(cost_curve), FadeIn(key_panel), run_time=1.5)

        # Animate the descent
        start_x = -2.5
        dot = Dot(axes.c2p(start_x, start_x**2 + 1), color="#6AB04C", radius=0.12)

        new_key = Text("Gradient Points\\nDownhill", font_size=22, color=YELLOW)
        new_key.to_edge(RIGHT, buff=0.8).shift(UP * 1.0)

        with self.voiceover(text="The green dot starts with a wrong guess. Watch it slide down the curve, each step reducing the error.") as tracker:
            self.play(FadeOut(key_panel), FadeIn(new_key))
            self.play(FadeIn(dot, scale=1.5))

            positions = [-2.5, -1.8, -1.2, -0.7, -0.3, 0.0]
            for i in range(1, len(positions)):
                x_val = positions[i]
                self.play(
                    dot.animate.move_to(axes.c2p(x_val, x_val**2 + 1)),
                    run_time=0.5
                )
            self.play(Indicate(dot, color="#6AB04C", scale_factor=1.5))

        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(0.3)

        # ═══ SEGMENT 5: SUMMARY ═══
        with self.voiceover(text="Remember: gradient descent finds the best answer by taking small steps downhill. That is how machines learn.") as tracker:
            banner = RoundedRectangle(corner_radius=0.25, width=10, height=1.5)
            banner.set_fill("#0A2A0A", opacity=1).set_stroke("#6AB04C", width=3)
            banner_text = Text("Gradient Descent: Small Steps → Minimum Error", font_size=26, color="#6AB04C", weight=BOLD)
            banner_text.move_to(banner)
            self.play(FadeIn(VGroup(banner, banner_text), scale=1.1))

        self.wait(2.0)
"""
    },
    # ────────────────────────────────────────────────────────────────
    # ML: NEURAL NETWORK LAYER PATTERN
    # ────────────────────────────────────────────────────────────────
    {
        "title": "ML neural network layer visualization pattern",
        "content": """
# Pattern: Neural network with layers of nodes and weighted connections
from manim import *

class NeuralNetworkPattern(Scene):
    def construct(self):
        self.camera.background_color = "#0F0F1A"

        def make_layer(n_nodes, x_pos, color="#4FACFE"):
            nodes = VGroup()
            for i in range(n_nodes):
                c = Circle(radius=0.25, color=color, stroke_width=2)
                c.set_fill(color, opacity=0.15)
                y = (i - (n_nodes - 1) / 2) * 0.8
                c.move_to([x_pos, y, 0])
                nodes.add(c)
            return nodes

        input_layer = make_layer(3, -3, "#4FACFE")
        hidden_layer = make_layer(4, 0, "#F9CA24")
        output_layer = make_layer(2, 3, "#6AB04C")

        # Draw connections
        connections = VGroup()
        for src in input_layer:
            for dst in hidden_layer:
                line = Line(src.get_right(), dst.get_left(), color=GREY, stroke_width=0.8, stroke_opacity=0.4)
                connections.add(line)
        for src in hidden_layer:
            for dst in output_layer:
                line = Line(src.get_right(), dst.get_left(), color=GREY, stroke_width=0.8, stroke_opacity=0.4)
                connections.add(line)

        # Labels
        input_label = Text("Input", font_size=20, color="#4FACFE").next_to(input_layer, DOWN, buff=0.4)
        hidden_label = Text("Hidden", font_size=20, color="#F9CA24").next_to(hidden_layer, DOWN, buff=0.4)
        output_label = Text("Output", font_size=20, color="#6AB04C").next_to(output_layer, DOWN, buff=0.4)

        network = VGroup(connections, input_layer, hidden_layer, output_layer, input_label, hidden_label, output_label)
        network.scale_to_fit_width(config.frame_width - 3)

        self.play(LaggedStart(*[Create(c) for c in connections], lag_ratio=0.01), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(n, scale=1.3) for n in input_layer], lag_ratio=0.1))
        self.play(LaggedStart(*[FadeIn(n, scale=1.3) for n in hidden_layer], lag_ratio=0.1))
        self.play(LaggedStart(*[FadeIn(n, scale=1.3) for n in output_layer], lag_ratio=0.1))
        self.play(FadeIn(input_label), FadeIn(hidden_label), FadeIn(output_label))
"""
    },
    # ────────────────────────────────────────────────────────────────
    # BASIC DATA STRUCTURE PATTERNS
    # ────────────────────────────────────────────────────────────────
    {
        "title": "Array visualization pattern",
        "content": """
# Pattern: Visualizing arrays with rounded boxes
from manim import *
class ArrayExample(Scene):
    def construct(self):
        self.camera.background_color = "#0F0F1A"
        arr = [5, 2, 8, 1, 9]

        def make_cell(value, index):
            box = RoundedRectangle(corner_radius=0.1, width=1.1, height=1.1)
            box.set_stroke(color="#4FACFE", width=2)
            box.set_fill(color="#1A1A2E", opacity=1)
            val = Text(str(value), font_size=38, color=WHITE, weight=BOLD).move_to(box)
            idx = Text(str(index), font_size=22, color="#4FACFE").next_to(box, DOWN, buff=0.15)
            return VGroup(box, val, idx)

        cells = VGroup(*[make_cell(arr[i], i) for i in range(len(arr))])
        cells.arrange(RIGHT, buff=0.15).move_to(ORIGIN)
        self.play(LaggedStart(*[FadeIn(c, shift=UP*0.3) for c in cells], lag_ratio=0.1))

        # Pointer
        pointer = Triangle(color="#F9CA24").scale(0.2).rotate(PI)
        pointer.set_fill("#F9CA24", opacity=1).next_to(cells[0], UP, buff=0.15)
        self.play(FadeIn(pointer))

        # Highlight cell
        self.play(cells[0][0].animate.set_fill("#2A2A1E", opacity=1).set_stroke("#F9CA24", width=3))
        self.play(pointer.animate.next_to(cells[1], UP, buff=0.15))
"""
    },
    {
        "title": "Binary tree / graph node pattern",
        "content": """
# Pattern: Drawing tree nodes with circles and edges
from manim import *
class TreeExample(Scene):
    def construct(self):
        self.camera.background_color = "#0F0F1A"

        def make_node(value, position):
            circle = Circle(radius=0.4)
            circle.set_stroke("#4FACFE", width=2)
            circle.set_fill("#1A1A2E", opacity=1)
            label = Text(str(value), font_size=32, color=WHITE, weight=BOLD).move_to(circle)
            group = VGroup(circle, label).move_to(position)
            return group

        # Create nodes
        root = make_node(1, UP * 2)
        left = make_node(2, LEFT * 2)
        right = make_node(3, RIGHT * 2)

        # Create edges
        edge_l = Line(root.get_bottom(), left.get_top(), color="#4FACFE", stroke_width=2)
        edge_r = Line(root.get_bottom(), right.get_top(), color="#4FACFE", stroke_width=2)

        self.play(Create(edge_l), Create(edge_r))
        self.play(FadeIn(root), FadeIn(left), FadeIn(right))

        # Highlight a node
        self.play(root[0].animate.set_fill("#1A2A3A", opacity=1).set_stroke("#F9CA24", width=3))
"""
    },
    {
        "title": "Sorting bars pattern",
        "content": """
# Pattern: Bar chart for sorting algorithms
from manim import *
class SortingExample(Scene):
    def construct(self):
        self.camera.background_color = "#0F0F1A"
        values = [4, 2, 7, 1, 5, 3]

        def make_bar(value, index, max_val=8):
            height = value / max_val * 4
            bar = Rectangle(width=0.7, height=height)
            bar.set_fill("#4FACFE", opacity=0.8)
            bar.set_stroke("#00F2FE", width=1)
            label = Text(str(value), font_size=26, color=WHITE).next_to(bar, UP, buff=0.1)
            group = VGroup(bar, label)
            group.move_to(RIGHT * (index - len(values)/2 + 0.5) * 0.9 + DOWN * (4 - height)/2)
            return group

        bars = VGroup(*[make_bar(v, i) for i, v in enumerate(values)])
        self.play(LaggedStart(*[FadeIn(b, shift=UP*0.2) for b in bars], lag_ratio=0.1))

        # Highlight bars being compared
        self.play(bars[0][0].animate.set_fill("#F9CA24", opacity=0.9))
        self.play(bars[1][0].animate.set_fill("#F9CA24", opacity=0.9))

        # Swap animation
        self.play(bars[0].animate.move_to(bars[1].get_center()),
                  bars[1].animate.move_to(bars[0].get_center()))
"""
    },
    {
        "title": "Mathematical function and graph pattern",
        "content": """
# Pattern: Drawing mathematical functions with axes
from manim import *
class MathExample(Scene):
    def construct(self):
        self.camera.background_color = "#0F0F1A"

        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-2, 6, 1],
            axis_config={"color": "#4FACFE", "stroke_width": 2},
            tips=True
        )
        x_label = axes.get_x_axis_label("x", color="#4FACFE")
        y_label = axes.get_y_axis_label("f(x)", color="#4FACFE")

        self.play(Create(axes), Write(x_label), Write(y_label))

        # Draw a function — ALWAYS use .plot() not .get_graph()
        curve = axes.plot(lambda x: x**2, color="#F9CA24", stroke_width=3)
        self.play(Create(curve), run_time=2)

        # Highlight a point
        dot = Dot(axes.c2p(1, 1), color="#6AB04C", radius=0.1)
        self.play(FadeIn(dot))
"""
    },
    {
        "title": "Step by step highlight pattern",
        "content": """
# Pattern: Step by step code or process highlighting
from manim import *
class StepExample(Scene):
    def construct(self):
        self.camera.background_color = "#0F0F1A"

        # Status display at bottom
        def make_status(text):
            msg = Text(text, font_size=28, color=WHITE)
            msg.to_edge(DOWN, buff=0.5)
            box = SurroundingRectangle(msg, color="#4FACFE", buff=0.2, corner_radius=0.1)
            return VGroup(box, msg)

        status = make_status("Starting...")
        self.play(FadeIn(status))

        new_status = make_status("Step 1 complete!")
        self.play(Transform(status, new_status))

        # Result banner
        result = RoundedRectangle(corner_radius=0.2, width=6, height=1.2)
        result.set_fill("#0A2A0A", opacity=1).set_stroke("#6AB04C", width=3)
        result_text = Text("Complete!", font_size=36, color="#6AB04C", weight=BOLD).move_to(result)
        self.play(FadeIn(VGroup(result, result_text), scale=1.2))
"""
    },
    {
        "title": "Linked list pattern",
        "content": """
# Pattern: Linked list with nodes and arrows
from manim import *
class LinkedListExample(Scene):
    def construct(self):
        self.camera.background_color = "#0F0F1A"
        values = [10, 20, 30, 40]

        def make_node(value):
            val_box = Rectangle(width=0.9, height=0.9)
            val_box.set_stroke("#4FACFE", width=2).set_fill("#1A1A2E", opacity=1)
            val_text = Text(str(value), font_size=32, color=WHITE, weight=BOLD).move_to(val_box)
            next_box = Rectangle(width=0.45, height=0.9)
            next_box.set_stroke("#4FACFE", width=2).set_fill("#0F0F2A", opacity=1)
            next_box.next_to(val_box, RIGHT, buff=0)
            next_text = Text("→", font_size=24, color="#4FACFE").move_to(next_box)
            return VGroup(val_box, val_text, next_box, next_text)

        nodes = VGroup(*[make_node(v) for v in values])
        nodes.arrange(RIGHT, buff=0.5).move_to(ORIGIN)

        arrows = VGroup(*[
            Arrow(nodes[i].get_right(), nodes[i+1].get_left(),
                  color="#4FACFE", buff=0.05, stroke_width=2)
            for i in range(len(nodes)-1)
        ])

        self.play(LaggedStart(*[FadeIn(n, shift=RIGHT*0.3) for n in nodes], lag_ratio=0.15))
        self.play(LaggedStart(*[Create(a) for a in arrows], lag_ratio=0.1))
""",
    },
    # ────────────────────────────────────────────────────────────────
    # ANTI-PATTERN: Hallucinated APIs that DO NOT EXIST in Manim
    # ────────────────────────────────────────────────────────────────
    {
        "title": "Hallucinated Manim APIs — classes and methods that DO NOT EXIST",
        "content": """
# CRITICAL: These APIs are frequently hallucinated by LLMs. NONE of them exist.
#
# ❌ SurroundingRoundedRectangle — DOES NOT EXIST (NameError)
#   ✅ Use: SurroundingRectangle(mobject, corner_radius=0.1, color=YELLOW)
#
# ❌ Text.set_text("new text") — Text is IMMUTABLE in Manim CE
#   ✅ Use: new_text = Text("new text", ...); self.play(Transform(old, new_text))
#
# ❌ .to_center() — does NOT exist on any Mobject
#   ✅ Use: .move_to(ORIGIN)
#
# ❌ Axes.get_graph(lambda x: ...) — DEPRECATED in Manim 0.18+
#   ✅ Use: axes.plot(lambda x: ..., color=YELLOW)
#
# ❌ Axes.get_vertical_line_to_graph(...) — DEPRECATED
#   ✅ Use: axes.get_vertical_line(axes.c2p(x, y))
#
# ❌ Text(alignment="left") — Text does NOT accept alignment=
#   ✅ Use: VGroup(t1, t2).arrange(DOWN, aligned_edge=LEFT)
#
# ❌ Text(max_width=5) — Text does NOT accept max_width=
#   ✅ Use: my_text = Text("..."); my_text.scale_to_fit_width(5)
#
# ❌ Text(justify=True) — Text does NOT accept justify=
#
# ❌ Paragraph(width=5) — width= is NOT a layout constraint in Manim v0.20.1
#   ✅ Use: VGroup of separate Text() lines + .scale_to_fit_width(5)
#
# ❌ .get_part_by_text("string") on Paragraph/Text — crashes with getter() error
#   ✅ Use: Split into separate Text() objects, Indicate each directly
#
# ❌ Rectangle(corner_radius=0.2) — Rectangle does NOT accept corner_radius
#   ✅ Use: RoundedRectangle(corner_radius=0.2, width=W, height=H)
#
# ❌ Line(start, end, opacity=0.3) — geometry constructors reject bare opacity=
#   ✅ Use: Line(start, end, stroke_opacity=0.3) or Circle(fill_opacity=0.5)
#
# ❌ ORANGE_E, PINK_C, WHITE_A, BLACK_D — these color variants DO NOT EXIST
#   ✅ ORANGE, PINK, WHITE, BLACK have NO suffix variants. Use base name or hex.
#   ✅ Colors WITH _A-_E: RED, BLUE, GREEN, YELLOW, GOLD, TEAL, PURPLE, MAROON, GREY
"""
    },
    # ────────────────────────────────────────────────────────────────
    # MathTex / LaTeX CORRECT USAGE
    # ────────────────────────────────────────────────────────────────
    {
        "title": "MathTex and Tex — correct LaTeX usage in Manim",
        "content": """
# Pattern: Using MathTex and Tex for mathematical expressions
from manim import *

class MathTexExample(Scene):
    def construct(self):
        self.camera.background_color = "#0F0F1A"

        # ✅ MathTex for math expressions (auto math mode)
        formula = MathTex(r"E = mc^2", font_size=48, color="#4FACFE")
        formula.to_edge(UP, buff=1.0)
        self.play(Write(formula))

        # ✅ MathTex with multiple parts (for selective coloring)
        equation = MathTex(r"f(x)", r"=", r"x^2 + 2x + 1", font_size=36)
        equation.set_color_by_tex("f(x)", "#4FACFE")
        equation.set_color_by_tex("x^2", "#F9CA24")
        equation.next_to(formula, DOWN, buff=0.8)
        self.play(Write(equation))

        # ✅ Tex for mixed text and math
        mixed = Tex(r"The area is $A = \\pi r^2$", font_size=30, color=WHITE)
        mixed.next_to(equation, DOWN, buff=0.8)
        self.play(Write(mixed))

        # ✅ Transform one equation into another
        new_eq = MathTex(r"f(x)", r"=", r"(x+1)^2", font_size=36)
        new_eq.move_to(equation)
        self.play(TransformMatchingTex(equation, new_eq))

        # ✅ Axis labels with Tex (correct — pass color to Tex, NOT to get_x_axis_label)
        axes = Axes(x_range=[-3, 3], y_range=[-2, 5])
        x_label = axes.get_x_axis_label(Tex(r"$x$", color=WHITE))
        y_label = axes.get_y_axis_label(Tex(r"$f(x)$", color=WHITE))
        # ❌ WRONG: axes.get_x_axis_label(Tex("x"), color=WHITE) — color= not accepted
        self.play(Create(axes), Write(x_label), Write(y_label))

        self.wait(1.0)
"""
    },
    # ────────────────────────────────────────────────────────────────
    # OPACITY API — stroke_opacity vs fill_opacity vs bare opacity
    # ────────────────────────────────────────────────────────────────
    {
        "title": "Opacity API rules — stroke_opacity vs fill_opacity (constructors reject bare opacity=)",
        "content": """
# CRITICAL: Manim geometry CONSTRUCTORS reject bare `opacity=` parameter.
# This causes: TypeError: Mobject.__init__() got an unexpected keyword argument 'opacity'
#
# RULE: Use stroke_opacity= for stroke objects, fill_opacity= for fill objects.
from manim import *

class OpacityExample(Scene):
    def construct(self):
        self.camera.background_color = "#0F0F1A"

        # ✅ CORRECT — stroke-based objects use stroke_opacity=
        line = Line(LEFT * 2, RIGHT * 2, color=BLUE, stroke_opacity=0.5)
        arrow = Arrow(LEFT, RIGHT, color=RED, stroke_opacity=0.7)
        dashed = DashedLine(UP, DOWN, color=GREY, stroke_opacity=0.3)

        # ✅ CORRECT — fill-based objects use fill_opacity=
        circle = Circle(radius=1, color="#4FACFE", fill_opacity=0.5)
        rect = RoundedRectangle(corner_radius=0.15, width=3, height=1.5)
        rect.set_fill("#1A1A2E", opacity=0.8)  # .set_fill() DOES accept opacity=
        rect.set_stroke("#F9CA24", width=2)

        # ❌ WRONG — these CRASH:
        # line_bad = Line(LEFT, RIGHT, opacity=0.5)        # TypeError!
        # arrow_bad = Arrow(LEFT, RIGHT, opacity=0.3)      # TypeError!
        # circle_bad = Circle(radius=1, opacity=0.5)       # TypeError!

        # ✅ Alternative: create first, then set opacity
        dot = Dot(ORIGIN, color=GREEN)
        dot.set_opacity(0.6)  # This works on any mobject

        self.play(Create(line), Create(arrow), Create(dashed))
        self.play(FadeIn(circle), FadeIn(rect), FadeIn(dot))
        self.wait(1.0)
"""
    },
    # ────────────────────────────────────────────────────────────────
    # Rectangle vs RoundedRectangle — corner_radius constraint
    # ────────────────────────────────────────────────────────────────
    {
        "title": "Rectangle vs RoundedRectangle — corner_radius only on RoundedRectangle",
        "content": """
# CRITICAL: Rectangle() does NOT accept corner_radius=
# This causes: TypeError: Mobject.__init__() got an unexpected keyword argument 'corner_radius'
from manim import *

class RectangleExample(Scene):
    def construct(self):
        self.camera.background_color = "#0F0F1A"

        # ✅ Sharp corners → use Rectangle
        sharp_box = Rectangle(width=3, height=1.5)
        sharp_box.set_stroke("#4FACFE", width=2)
        sharp_box.set_fill("#1A1A2E", opacity=1)

        # ✅ Rounded corners → use RoundedRectangle
        rounded_box = RoundedRectangle(corner_radius=0.2, width=3, height=1.5)
        rounded_box.set_stroke("#F9CA24", width=2)
        rounded_box.set_fill("#1A1A2E", opacity=1)

        # ❌ WRONG — this CRASHES:
        # bad_box = Rectangle(width=3, height=1.5, corner_radius=0.2)  # TypeError!

        # ✅ SurroundingRectangle with corner_radius IS valid
        label = Text("Hello", font_size=28, color=WHITE)
        highlight = SurroundingRectangle(label, corner_radius=0.1, color=YELLOW, buff=0.2)

        VGroup(sharp_box, rounded_box).arrange(RIGHT, buff=1.0).move_to(UP)
        label.move_to(DOWN)

        self.play(FadeIn(sharp_box), FadeIn(rounded_box))
        self.play(FadeIn(label), Create(highlight))
        self.wait(1.0)
"""
    },
    # ────────────────────────────────────────────────────────────────
    # ValueTracker + Updater pattern for dynamic animations
    # ────────────────────────────────────────────────────────────────
    {
        "title": "ValueTracker and updater pattern — dynamic animations",
        "content": """
# Pattern: Using ValueTracker with always_redraw for smooth dynamic animations
from manim import *

class ValueTrackerExample(Scene):
    def construct(self):
        self.camera.background_color = "#0F0F1A"

        axes = Axes(
            x_range=[-3, 3, 1], y_range=[-2, 6, 1],
            axis_config={"color": "#4FACFE", "stroke_width": 2}
        )
        curve = axes.plot(lambda x: x**2, color="#F9CA24", stroke_width=3)
        self.play(Create(axes), Create(curve))

        # ValueTracker controls the x-position of a dot
        x_tracker = ValueTracker(-2.5)

        # always_redraw redraws the dot every frame at the tracked position
        dot = always_redraw(lambda: Dot(
            axes.c2p(x_tracker.get_value(), x_tracker.get_value()**2),
            color="#6AB04C", radius=0.12
        ))

        # always_redraw for a vertical dashed line
        v_line = always_redraw(lambda: DashedLine(
            axes.c2p(x_tracker.get_value(), 0),
            axes.c2p(x_tracker.get_value(), x_tracker.get_value()**2),
            color=GREY, stroke_width=1.5
        ))

        # Dynamic label showing current x value
        label = always_redraw(lambda: Text(
            f"x = {x_tracker.get_value():.1f}",
            font_size=22, color=WHITE
        ).next_to(dot, UR, buff=0.2))

        self.play(FadeIn(dot), Create(v_line), FadeIn(label))

        # Animate the tracker — dot, line, and label move smoothly
        self.play(x_tracker.animate.set_value(2.5), run_time=4, rate_func=smooth)
        self.wait(1.0)
"""
    },
    # ────────────────────────────────────────────────────────────────
    # STACK / QUEUE visualization pattern
    # ────────────────────────────────────────────────────────────────
    {
        "title": "Stack and queue visualization pattern",
        "content": """
# Pattern: Stack (LIFO) and Queue (FIFO) with push/pop animations
from manim import *

class StackExample(Scene):
    def construct(self):
        self.camera.background_color = "#0F0F1A"

        # Stack container
        container = Rectangle(width=2.0, height=4.5)
        container.set_stroke("#4FACFE", width=2)
        container.set_fill("#0A0A1A", opacity=0.5)
        container.move_to(ORIGIN)
        stack_label = Text("STACK", font_size=24, color="#4FACFE").next_to(container, UP, buff=0.3)
        self.play(Create(container), FadeIn(stack_label))

        # Push elements
        stack_items = []
        values = [10, 20, 30]
        for i, val in enumerate(values):
            box = RoundedRectangle(corner_radius=0.08, width=1.6, height=0.7)
            box.set_fill("#1A1A2E", opacity=1).set_stroke("#4FACFE", width=2)
            txt = Text(str(val), font_size=28, color=WHITE, weight=BOLD).move_to(box)
            item = VGroup(box, txt)
            # Stack grows from bottom
            y_pos = container.get_bottom()[1] + 0.5 + i * 0.85
            item.move_to([container.get_center()[0], y_pos, 0])

            # Push animation: item enters from above
            item.save_state()
            item.move_to(container.get_top() + UP * 1.0)
            self.play(item.animate.restore(), run_time=0.6)
            stack_items.append(item)

        # Pop (LIFO): remove top element
        top = stack_items.pop()
        self.play(top.animate.shift(RIGHT * 3), run_time=0.5)
        self.play(
            top[0].animate.set_fill("#2A0A0A", opacity=1).set_stroke(RED, width=2),
            run_time=0.3
        )
        pop_label = Text("Popped!", font_size=22, color=RED).next_to(top, UP, buff=0.2)
        self.play(FadeIn(pop_label))
        self.wait(1.0)
"""
    },
]


def chunk_python_file(content: str, source: str) -> list:
    """Split a Python file into meaningful chunks by class/function."""
    chunks = []

    # Split by class definitions
    class_pattern = re.split(r'\n(?=class )', content)
    for section in class_pattern:
        if len(section.strip()) > 100:  # skip tiny chunks
            chunks.append({
                "content": section.strip()[:2000],  # limit size
                "source": source
            })

    # If no classes found, split by functions
    if len(chunks) <= 1:
        func_pattern = re.split(r'\n(?=def )', content)
        for section in func_pattern:
            if len(section.strip()) > 100:
                chunks.append({
                    "content": section.strip()[:2000],
                    "source": source
                })

    return chunks


def download_and_chunk_docs():
    """Download Manim source files and chunk them."""
    all_chunks = []

    # Add handcrafted patterns first — these are highest quality
    print("Adding handcrafted animation patterns...")
    for pattern in HANDCRAFTED_PATTERNS:
        all_chunks.append({
            "content": pattern["content"],
            "source": pattern["title"]
        })
    print(f"Added {len(HANDCRAFTED_PATTERNS)} handcrafted patterns")

    # Download Manim source docs
    print("\nDownloading Manim documentation...")
    for url in MANIM_DOC_URLS:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                filename = url.split("/")[-1]
                chunks = chunk_python_file(response.text, filename)
                all_chunks.extend(chunks)
                print(f"  ✅ {filename} → {len(chunks)} chunks")
            else:
                print(f"  ❌ Failed: {url.split('/')[-1]}")
        except Exception as e:
            print(f"  ❌ Error: {url.split('/')[-1]} — {e}")

    print(f"\nTotal chunks: {len(all_chunks)}")
    return all_chunks


def build_faiss_index(chunks: list):
    """Build FAISS vector search index from chunks."""
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np

    print("\nBuilding search index...")
    print("Loading embedding model (first time takes 1-2 minutes)...")

    model = SentenceTransformer('all-MiniLM-L6-v2')

    texts = [c["content"] for c in chunks]
    print(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True)

    # Build FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings, dtype=np.float32))

    return index, embeddings


if __name__ == "__main__":
    os.makedirs("rag", exist_ok=True)

    # Step 1: Download and chunk docs
    chunks = download_and_chunk_docs()

    # Step 2: Save chunks
    with open("rag/manim_chunks.json", "w") as f:
        json.dump(chunks, f)
    print("\n✅ Chunks saved to rag/manim_chunks.json")

    # Step 3: Build FAISS index
    index, embeddings = build_faiss_index(chunks)

    # Step 4: Save index
    import faiss
    faiss.write_index(index, "rag/manim_docs.index")
    print("✅ FAISS index saved to rag/manim_docs.index")

    print("\n🎉 RAG setup complete!")
    print(f"   {len(chunks)} chunks indexed and ready to search")