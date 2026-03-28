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
    "https://raw.githubusercontent.com/ManimCommunity/manim/main/manim/mobject/coordinate_systems.py",
    # Manim-Voiceover source docs
    "https://raw.githubusercontent.com/ManimCommunity/manim-voiceover/main/manim_voiceover/voiceover_scene.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim-voiceover/main/manim_voiceover/services/gtts.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim-voiceover/main/manim_voiceover/tracker.py",
    "https://raw.githubusercontent.com/ManimCommunity/manim-voiceover/main/manim_voiceover/helper.py",
]

# Also add handcrafted pattern examples for common animation types
HANDCRAFTED_PATTERNS = [
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
        
        # Draw a function
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
            # Value box
            val_box = Rectangle(width=0.9, height=0.9)
            val_box.set_stroke("#4FACFE", width=2).set_fill("#1A1A2E", opacity=1)
            val_text = Text(str(value), font_size=32, color=WHITE, weight=BOLD).move_to(val_box)
            # Next pointer box
            next_box = Rectangle(width=0.45, height=0.9)
            next_box.set_stroke("#4FACFE", width=2).set_fill("#0F0F2A", opacity=1)
            next_box.next_to(val_box, RIGHT, buff=0)
            next_text = Text("→", font_size=24, color="#4FACFE").move_to(next_box)
            return VGroup(val_box, val_text, next_box, next_text)
        
        nodes = VGroup(*[make_node(v) for v in values])
        nodes.arrange(RIGHT, buff=0.5).move_to(ORIGIN)
        
        # Arrows between nodes
        arrows = VGroup(*[
            Arrow(nodes[i].get_right(), nodes[i+1].get_left(),
                  color="#4FACFE", buff=0.05, stroke_width=2)
            for i in range(len(nodes)-1)
        ])
        
        self.play(LaggedStart(*[FadeIn(n, shift=RIGHT*0.3) for n in nodes], lag_ratio=0.15))
        self.play(LaggedStart(*[Create(a) for a in arrows], lag_ratio=0.1))
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
    }
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