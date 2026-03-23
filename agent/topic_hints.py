"""
Static topic-to-visual-pattern lookup table.

Maps common educational topic keywords to recommended visual styles,
layout hints, and animation patterns. This gives the Planner instant
context about how a topic is *typically* animated in professional
educational content (like 3Blue1Brown, Khan Academy, etc.), avoiding
weird or ineffective visual choices without needing a web search.

Usage:
    from agent.topic_hints import get_topic_hints
    hints = get_topic_hints("bubble sort algorithm")
    # Returns a dict with visual_style, layout_tips, common_elements, etc.
"""

from typing import Optional


# Each entry maps a set of keywords to visual recommendations.
# The planner and coder prompts can use these hints to make better choices.
TOPIC_VISUAL_HINTS = {
    # ── Sorting Algorithms ──────────────────────────────────────────
    "sorting": {
        "keywords": ["sort", "sorting", "bubble sort", "merge sort", "quick sort",
                      "insertion sort", "selection sort", "heap sort", "radix sort"],
        "visual_style": "bar_chart",
        "layout_tips": [
            "Use vertical bars whose height represents value — this is the standard for sorting visualizations.",
            "Highlight the two elements being compared with a bright color (e.g., yellow).",
            "Show swaps with smooth Transform animations, not teleportation.",
            "Keep array indices visible below each bar.",
            "For arrays >10 elements, split into 2 rows or use narrower bars.",
            "Add a 'sorted' color (green) to elements that reach their final position.",
        ],
        "common_elements": ["bars", "index_labels", "comparison_arrows", "sorted_markers"],
        "max_simultaneous_objects": 12,
        "avoid": ["Do not use circles or nodes for sorting — bars are universally expected."],
    },

    # ── Search Algorithms ───────────────────────────────────────────
    "searching": {
        "keywords": ["search", "binary search", "linear search", "searching"],
        "visual_style": "array_boxes",
        "layout_tips": [
            "Use a horizontal row of boxes with values inside — standard for search visualization.",
            "Highlight the current search window with a colored border.",
            "For binary search: show low/high pointers as arrows below the array.",
            "Gray out eliminated elements to show progress.",
            "Show the target value prominently above or beside the array.",
        ],
        "common_elements": ["value_boxes", "pointer_arrows", "target_label", "eliminated_overlay"],
        "max_simultaneous_objects": 10,
        "avoid": ["Do not show all comparisons simultaneously — reveal them one at a time."],
    },

    # ── Trees & Graphs ──────────────────────────────────────────────
    "tree": {
        "keywords": ["tree", "binary tree", "bst", "binary search tree", "avl",
                      "red-black tree", "heap", "trie", "traversal", "inorder",
                      "preorder", "postorder", "bfs", "dfs", "breadth first", "depth first"],
        "visual_style": "diagram",
        "layout_tips": [
            "Use circles for nodes with values inside, and lines/arrows for edges.",
            "Layout: root at top, children below. Use Manim's Tree/Graph layout or manual positioning.",
            "Scale the ENTIRE tree group to fit within frame after construction — this is critical.",
            "For traversal: highlight the current node with a bright color, and dim visited nodes.",
            "Show the traversal order as a growing list at the bottom of the screen.",
            "For trees with >7 nodes: use smaller node radius (0.3) and font_size=20.",
            "CRITICAL: After building the full tree, call .scale_to_fit_width(config.frame_width - 3) to prevent overflow.",
        ],
        "common_elements": ["node_circles", "edge_lines", "value_labels", "traversal_list"],
        "max_simultaneous_objects": 15,
        "avoid": ["Do not try to animate a tree with >15 nodes — it will overflow the frame."],
    },

    # ── Linked Lists ────────────────────────────────────────────────
    "linked_list": {
        "keywords": ["linked list", "singly linked", "doubly linked", "linkedlist"],
        "visual_style": "array_boxes",
        "layout_tips": [
            "Use boxes with arrows pointing to the next node — the classic linked list visualization.",
            "Arrange horizontally with arrows between boxes.",
            "For >5 nodes: wrap to a second row or use smaller boxes.",
            "Highlight the current pointer with a different color during traversal.",
            "Show null/None at the end with a special symbol.",
        ],
        "common_elements": ["node_boxes", "next_arrows", "pointer_label", "null_marker"],
        "max_simultaneous_objects": 8,
        "avoid": [],
    },

    # ── Stacks & Queues ─────────────────────────────────────────────
    "stack_queue": {
        "keywords": ["stack", "queue", "push", "pop", "enqueue", "dequeue", "fifo", "lifo"],
        "visual_style": "array_boxes",
        "layout_tips": [
            "For stacks: show vertical column of boxes, new elements added on top.",
            "For queues: show horizontal row, elements enter from right, exit from left.",
            "Animate push/enqueue with FadeIn + shift, pop/dequeue with FadeOut + shift.",
            "Show a pointer/label for 'top' (stack) or 'front'/'rear' (queue).",
        ],
        "common_elements": ["element_boxes", "top_pointer", "operation_label"],
        "max_simultaneous_objects": 8,
        "avoid": [],
    },

    # ── Math Functions & Equations ──────────────────────────────────
    "math": {
        "keywords": ["equation", "function", "graph", "parabola", "quadratic",
                      "linear", "polynomial", "derivative", "integral", "calculus",
                      "sine", "cosine", "trigonometry", "algebra", "slope",
                      "tangent line", "limit", "differentiation", "integration"],
        "visual_style": "graph_plot",
        "layout_tips": [
            "Use Axes() or NumberPlane() for coordinate systems.",
            "Plot functions with smooth curves using plot() or ParametricFunction().",
            "Show the equation in MathTex at the top or corner of the screen.",
            "For derivatives: show the tangent line moving along the curve.",
            "For integrals: shade the area under the curve progressively.",
            "Use color-coding: function in one color, derivative in another.",
        ],
        "common_elements": ["axes", "function_curve", "equation_tex", "labels", "shaded_area"],
        "max_simultaneous_objects": 8,
        "avoid": ["Do not use bar charts for math functions — use proper coordinate plots."],
    },

    # ── Physics ─────────────────────────────────────────────────────
    "physics": {
        "keywords": ["physics", "force", "velocity", "acceleration", "momentum",
                      "gravity", "projectile", "newton", "motion", "wave",
                      "pendulum", "spring", "friction", "energy", "work",
                      "electric", "magnetic", "circuit", "optics", "lens",
                      "reflection", "refraction"],
        "visual_style": "physics_motion",
        "layout_tips": [
            "Use arrows for force vectors — length proportional to magnitude.",
            "Animate motion with smooth path animations (MoveAlongPath or shift).",
            "Show formulas alongside the visual demonstration.",
            "For projectile motion: trace the parabolic path as the object moves.",
            "For waves: use sine curves with progressive animation.",
            "Label all forces, velocities, and angles clearly.",
        ],
        "common_elements": ["force_arrows", "moving_object", "path_trace", "formula_tex", "labels"],
        "max_simultaneous_objects": 10,
        "avoid": ["Do not use static diagrams for physics — motion must be animated."],
    },

    # ── Biology ─────────────────────────────────────────────────────
    "biology": {
        "keywords": ["biology", "cell", "dna", "rna", "protein", "mitosis",
                      "meiosis", "photosynthesis", "respiration", "evolution",
                      "genetics", "chromosome", "enzyme", "organism", "ecosystem",
                      "nucleus", "membrane", "organ"],
        "visual_style": "diagram",
        "layout_tips": [
            "Use labeled diagrams with clear component identification.",
            "For processes (photosynthesis, respiration): show flowchart-style step progression.",
            "For cell structure: show cross-section with labeled parts.",
            "For DNA: use the classic double-helix representation or simplified ladder.",
            "Use arrows to show process flow (input → process → output).",
            "Color-code different components for easy identification.",
        ],
        "common_elements": ["labeled_shapes", "process_arrows", "component_labels", "legend"],
        "max_simultaneous_objects": 10,
        "avoid": ["Do not overcrowd — show one process phase at a time, then transition."],
    },

    # ── Chemistry ───────────────────────────────────────────────────
    "chemistry": {
        "keywords": ["chemistry", "atom", "molecule", "reaction", "bond",
                      "element", "compound", "periodic table", "electron",
                      "proton", "neutron", "orbital", "ionic", "covalent",
                      "acid", "base", "pH", "oxidation", "reduction"],
        "visual_style": "diagram",
        "layout_tips": [
            "For atomic structure: show nucleus with orbiting electrons.",
            "For reactions: show reactants on left, arrow in middle, products on right.",
            "Use color-coded circles for different atoms.",
            "For bonds: show shared electron pairs with lines between atoms.",
            "Animate reaction progression from reactants to products.",
        ],
        "common_elements": ["atom_circles", "bond_lines", "reaction_arrow", "element_labels"],
        "max_simultaneous_objects": 10,
        "avoid": [],
    },

    # ── History & Timelines ─────────────────────────────────────────
    "history": {
        "keywords": ["history", "timeline", "war", "revolution", "civilization",
                      "empire", "dynasty", "century", "era", "period",
                      "independence", "constitution"],
        "visual_style": "timeline",
        "layout_tips": [
            "Use a horizontal timeline with labeled points for key events.",
            "Reveal events progressively from left to right.",
            "Use icons or small images at each timeline point.",
            "Show dates clearly below or above each event.",
            "Group related events with colored segments.",
        ],
        "common_elements": ["timeline_line", "event_markers", "date_labels", "event_descriptions"],
        "max_simultaneous_objects": 8,
        "avoid": ["Do not show all events at once — reveal them sequentially."],
    },

    # ── Flowcharts & Processes ──────────────────────────────────────
    "process": {
        "keywords": ["process", "flowchart", "algorithm", "workflow", "decision",
                      "if else", "conditional", "loop", "iteration", "recursion",
                      "step by step", "procedure"],
        "visual_style": "flowchart",
        "layout_tips": [
            "Use standard flowchart shapes: rectangles for process, diamonds for decisions, ovals for start/end.",
            "Arrange top-to-bottom or left-to-right with clear arrows.",
            "Highlight the current step during walkthrough.",
            "Use color to distinguish different types of steps.",
            "For >5 steps: show portions at a time, scrolling or transitioning between groups.",
        ],
        "common_elements": ["process_boxes", "decision_diamonds", "flow_arrows", "labels"],
        "max_simultaneous_objects": 8,
        "avoid": ["Do not create overly complex flowcharts — simplify to 5-7 key steps."],
    },

    # ── Networking & Systems ────────────────────────────────────────
    "networking": {
        "keywords": ["network", "internet", "tcp", "ip", "http", "dns",
                      "server", "client", "protocol", "router", "packet",
                      "osi model", "api", "request", "response", "database"],
        "visual_style": "diagram",
        "layout_tips": [
            "Use icons/boxes for servers, clients, routers, databases.",
            "Show data flow with animated arrows between components.",
            "For layered models (OSI, TCP/IP): show horizontal layers stacked vertically.",
            "Animate packet/request movement from source to destination.",
            "Label each component and connection clearly.",
        ],
        "common_elements": ["component_boxes", "connection_arrows", "data_packets", "labels"],
        "max_simultaneous_objects": 8,
        "avoid": [],
    },
}


def get_topic_hints(query: str) -> Optional[dict]:
    """
    Match a user query against known topic patterns and return
    visual hints for the Planner/Coder.

    Returns None if no matching topic is found.
    """
    query_lower = query.lower()

    best_match = None
    best_score = 0

    for category, hints in TOPIC_VISUAL_HINTS.items():
        score = 0
        for keyword in hints["keywords"]:
            if keyword in query_lower:
                # Longer keyword matches are more specific, so weight them higher
                score += len(keyword)

        if score > best_score:
            best_score = score
            best_match = hints

    if best_match and best_score > 0:
        # Return a copy without the keywords list (not needed downstream)
        result = {k: v for k, v in best_match.items() if k != "keywords"}
        return result

    return None


def format_hints_for_prompt(hints: Optional[dict]) -> str:
    """
    Format topic hints into a readable string for injection into prompts.
    Returns empty string if no hints available.
    """
    if not hints:
        return ""

    parts = []
    parts.append(f"Recommended visual style: {hints.get('visual_style', 'diagram')}")
    parts.append(f"Max simultaneous on-screen objects: {hints.get('max_simultaneous_objects', 8)}")

    layout_tips = hints.get("layout_tips", [])
    if layout_tips:
        tips_str = "\n".join(f"  - {tip}" for tip in layout_tips)
        parts.append(f"Layout tips:\n{tips_str}")

    common_elements = hints.get("common_elements", [])
    if common_elements:
        parts.append(f"Common elements: {', '.join(common_elements)}")

    avoid = hints.get("avoid", [])
    if avoid:
        avoid_str = "\n".join(f"  - {a}" for a in avoid)
        parts.append(f"Avoid:\n{avoid_str}")

    return "\n".join(parts)
