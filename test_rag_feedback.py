"""
Test RAG and Feedback integration into the AnimAI Studio pipeline.
Validates that:
1. RAG retriever returns results for relevant queries (or gracefully degrades)
2. Feedback examples are properly formatted for prompt injection
3. Coder prompt includes RAG and feedback sections when data is available
4. System works correctly when RAG/feedback data is empty (graceful fallback)
"""

import json
import os
import sys


def test_rag_retriever():
    """Test that the RAG retriever works or gracefully falls back."""
    print("\n" + "=" * 60)
    print("TEST 1: RAG Retriever")
    print("=" * 60)

    from rag.retriever import retrieve

    # Test retrieval
    result = retrieve("animate binary search on an array")

    if result:
        print(f"✅ RAG returned {len(result)} chars of context")
        # Verify it contains meaningful content
        assert len(result) > 50, "RAG result should be substantial"
        print(f"   Preview: {result[:100]}...")
    else:
        print("⚠️  RAG returned empty (index may not be built yet — this is OK, graceful fallback works)")

    # Test with voiceover query
    result_v = retrieve("VoiceoverScene GTTSService voiceover")
    if result_v:
        print(f"✅ Voiceover RAG returned {len(result_v)} chars")
    else:
        print("⚠️  Voiceover RAG returned empty (rebuild index with download_docs.py to include voiceover docs)")

    print("✅ PASSED: RAG retriever works without crashing")


def test_feedback_retrieval():
    """Test that feedback examples are retrieved and formatted correctly."""
    print("\n" + "=" * 60)
    print("TEST 2: Feedback Example Retrieval")
    print("=" * 60)

    from agent.feedback import get_learned_examples, get_feedback_stats

    stats = get_feedback_stats()
    print(f"Feedback stats: {stats}")

    # Test retrieval for a category that may have examples
    examples = get_learned_examples("array_boxes", k=2)
    print(f"array_boxes examples: {len(examples)}")

    if examples:
        for ex in examples:
            assert "query" in ex, "Example should have 'query'"
            assert "code" in ex, "Example should have 'code'"
            print(f"  - Query: {ex['query'][:60]}... (upvotes: {ex.get('upvotes', 0)})")
    else:
        print("  No examples yet — this is expected for a fresh install")

    # Test retrieval for a category with no examples
    empty = get_learned_examples("nonexistent_category", k=2)
    assert len(empty) == 0, "Should return empty for unknown category"
    print(f"nonexistent_category examples: {len(empty)} (expected 0)")

    print("✅ PASSED: Feedback retrieval works correctly")


def test_coder_rag_integration():
    """Test that the coder builds RAG context and feedback sections correctly."""
    print("\n" + "=" * 60)
    print("TEST 3: Coder RAG + Feedback Integration")
    print("=" * 60)

    from agent.coder import _build_rag_context, _build_feedback_section

    # Test RAG context builder
    rag_ctx = _build_rag_context("bubble sort algorithm")
    assert isinstance(rag_ctx, str), "RAG context should be a string"
    print(f"RAG context length: {len(rag_ctx)} chars")
    if "(no RAG context available)" in rag_ctx:
        print("  ⚠️  RAG returned fallback (index not built — OK for testing)")
    else:
        print(f"  ✅ RAG context preview: {rag_ctx[:80]}...")

    # Test feedback section builder
    feedback_section = _build_feedback_section("array_boxes")
    assert isinstance(feedback_section, str), "Feedback section should be a string"
    print(f"Feedback section length: {len(feedback_section)} chars")
    if feedback_section:
        assert "PROVEN EXAMPLES" in feedback_section, "Should have header"
        print(f"  ✅ Feedback section starts with: {feedback_section[:60]}...")
    else:
        print("  No feedback examples for this category — returns empty string (correct)")

    # Test with empty category
    empty_feedback = _build_feedback_section("nonexistent")
    assert empty_feedback == "", "Should return empty string for unknown category"
    print(f"Empty category feedback: '{empty_feedback}' (expected empty)")

    print("✅ PASSED: Coder integration helpers work correctly")


def test_prompt_formatting():
    """Test that the coder prompt correctly substitutes RAG and feedback placeholders."""
    print("\n" + "=" * 60)
    print("TEST 4: Prompt Placeholder Formatting")
    print("=" * 60)

    from agent.coder import CODER_PROMPT, REVISION_PROMPT

    # Verify placeholders exist
    assert "{manim_docs}" in CODER_PROMPT, "CODER_PROMPT should have {manim_docs} placeholder"
    assert "{feedback_examples}" in CODER_PROMPT, "CODER_PROMPT should have {feedback_examples} placeholder"
    assert "{manim_docs}" in REVISION_PROMPT, "REVISION_PROMPT should have {manim_docs} placeholder"
    print("✅ All placeholders present in prompts")

    # Test formatting works without errors
    formatted = CODER_PROMPT.format(
        query="test query",
        plan_json="{}",
        manim_docs="test docs context",
        feedback_examples="test feedback",
    )
    assert "test docs context" in formatted, "RAG context should appear in formatted prompt"
    assert "test feedback" in formatted, "Feedback should appear in formatted prompt"
    print("✅ CODER_PROMPT formats correctly with all placeholders")

    formatted_rev = REVISION_PROMPT.format(
        query="test",
        plan_json="{}",
        manim_docs="test docs",
        change_request="make it better",
        existing_code="pass",
    )
    assert "test docs" in formatted_rev, "RAG context should appear in revision prompt"
    print("✅ REVISION_PROMPT formats correctly with all placeholders")

    print("✅ PASSED: Prompt formatting works correctly")


def test_debugger_rag_integration():
    """Test that the debugger prompt has the RAG placeholder."""
    print("\n" + "=" * 60)
    print("TEST 5: Debugger RAG Integration")
    print("=" * 60)

    from agent.debugger import DEBUGGER_PROMPT

    assert "{manim_context}" in DEBUGGER_PROMPT, "DEBUGGER_PROMPT should have {manim_context} placeholder"
    print("✅ Debugger prompt has {manim_context} placeholder")

    # Test formatting
    formatted = DEBUGGER_PROMPT.format(
        code="from manim import *\npass",
        error="NameError: name 'BROWN' is not defined",
        manim_context="test manim API reference",
    )
    assert "test manim API reference" in formatted, "RAG context should appear in debugger prompt"
    print("✅ Debugger prompt formats correctly")

    print("✅ PASSED: Debugger RAG integration works correctly")


def test_download_docs_voiceover_urls():
    """Test that download_docs.py includes manim-voiceover URLs."""
    print("\n" + "=" * 60)
    print("TEST 6: Download Docs Voiceover URLs")
    print("=" * 60)

    from rag.download_docs import MANIM_DOC_URLS, HANDCRAFTED_PATTERNS

    voiceover_urls = [url for url in MANIM_DOC_URLS if "voiceover" in url.lower()]
    assert len(voiceover_urls) >= 3, f"Should have at least 3 voiceover URLs, found {len(voiceover_urls)}"
    print(f"✅ Found {len(voiceover_urls)} manim-voiceover URLs:")
    for url in voiceover_urls:
        print(f"   - {url.split('/')[-1]}")

    voiceover_patterns = [p for p in HANDCRAFTED_PATTERNS if "voiceover" in p["title"].lower()]
    assert len(voiceover_patterns) >= 1, "Should have at least 1 voiceover handcrafted pattern"
    print(f"✅ Found {len(voiceover_patterns)} voiceover handcrafted pattern(s)")

    print("✅ PASSED: Voiceover docs are configured for RAG indexing")


if __name__ == "__main__":
    print("\n🧪 Testing RAG & Feedback Integration")
    print("=" * 60)

    passed = 0
    failed = 0

    tests = [
        test_rag_retriever,
        test_feedback_retrieval,
        test_coder_rag_integration,
        test_prompt_formatting,
        test_debugger_rag_integration,
        test_download_docs_voiceover_urls,
    ]

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {test_fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ ERROR in {test_fn.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    if failed == 0:
        print("✅ ALL TESTS PASSED!")
    else:
        print(f"❌ {failed} test(s) failed")
    print("=" * 60)
