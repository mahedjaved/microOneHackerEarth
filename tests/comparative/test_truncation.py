"""
Test truncation hypothesis: does passage truncation cause zero support_probability?

Hypothesis: The 500-char truncation in ask_question.py cuts off supporting evidence
before the verifier sees it, causing support_probability=0.0 for questions that
should have support.

This script tests D1, D2, D5 (which show support_probability=0.0) with both
truncated and full passages to verify the hypothesis.
"""

import requests
import json
from pathlib import Path

BACKEND_URL = "http://127.0.0.1:8003"

# Questions that showed support_probability=0.0
TEST_QUESTIONS = [
    {
        "id": "D1",
        "question": "According to the aspirin document, what is the maximum single adult dose?",
        "expected_keywords": ["500", "mg", "dose", "single"],
    },
    {
        "id": "D2",
        "question": "What does the aspirin document say about administration with food?",
        "expected_keywords": ["food", "stomach", "irritation", "milk"],
    },
    {
        "id": "D5",
        "question": "According to the document, should aspirin be taken with food or on an empty stomach?",
        "expected_keywords": ["food", "stomach", "empty", "irritation"],
    },
]


def test_with_truncation():
    """Test with current 500-char truncation (via normal API)."""
    print("=" * 60)
    print("TEST WITH TRUNCATION (500 chars)")
    print("=" * 60)

    results = []
    for tc in TEST_QUESTIONS:
        print(f"\n[{tc['id']}] {tc['question'][:60]}...")
        try:
            response = requests.post(
                f"{BACKEND_URL}/ask/",
                data={"question": tc["question"]},
                timeout=90,
            )
            if response.status_code == 200:
                data = response.json()
                doubt_cert = data.get("doubt_certificate", {})
                support_prob = doubt_cert.get("support_probability", "N/A")
                conformal_set = doubt_cert.get("conformal_set", [])
                status = doubt_cert.get("status", "N/A")
                print(f"  support_probability: {support_prob}")
                print(f"  status: {status}")
                print(f"  conformal_set: {conformal_set}")
                results.append({
                    "id": tc["id"],
                    "support_probability": support_prob,
                    "status": status,
                    "truncated": True,
                })
            else:
                print(f"  ERROR: HTTP {response.status_code}")
                print(f"  Body: {response.text[:200]}")
        except Exception as e:
            print(f"  EXCEPTION: {e}")

    return results


def test_with_full_passages():
    """Test with full passages (direct Pinecone query, no truncation)."""
    print("\n" + "=" * 60)
    print("TEST WITH FULL PASSAGES (no truncation)")
    print("=" * 60)

    # Import backend modules to query Pinecone directly
    import sys
    backend_dir = Path(__file__).parent.parent / "backend"
    sys.path.insert(0, str(backend_dir))

    from server.modules.load_vectorstore import embedding_model, PINECONE_INDEX_NAME
    from server.config import settings
    from pinecone import Pinecone

    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(PINECONE_INDEX_NAME)

    results = []
    for tc in TEST_QUESTIONS:
        print(f"\n[{tc['id']}] {tc['question'][:60]}...")

        # Query Pinecone with full passages
        embedding_query = embedding_model.embed_query(tc["question"])
        response = index.query(
            vector=embedding_query,
            top_k=2,
            include_metadata=True,
        )

        # Get full passage text (no truncation)
        full_passages = []
        for match in response["matches"]:
            text = match["metadata"].get("text", "")
            full_passages.append({
                "text": text,
                "text_length": len(text),
                "score": match["score"],
            })

        print(f"  Retrieved {len(full_passages)} passages")
        for i, p in enumerate(full_passages):
            print(f"  Passage {i+1}: {p['text_length']} chars, score={p['score']:.3f}")
            # Show first 200 chars
            print(f"    Preview: {p['text'][:200]}...")

        # Check if expected keywords appear in full passages
        all_text = " ".join([p["text"].lower() for p in full_passages])
        found_keywords = [kw for kw in tc["expected_keywords"] if kw.lower() in all_text]
        missing_keywords = [kw for kw in tc["expected_keywords"] if kw.lower() not in all_text]

        print(f"  Expected keywords found: {found_keywords}")
        print(f"  Expected keywords missing: {missing_keywords}")

        # Check if truncation would cut off the relevant text
        truncated_text = " ".join([p["text"][:500].lower() for p in full_passages])
        found_after_trunc = [kw for kw in tc["expected_keywords"] if kw.lower() in truncated_text]
        lost_by_truncation = [kw for kw in found_keywords if kw not in found_after_trunc]

        if lost_by_truncation:
            print(f"  ⚠️  KEYWORDS LOST BY TRUNCATION: {lost_by_truncation}")
        else:
            print(f"  ✓  All found keywords survive truncation")

        results.append({
            "id": tc["id"],
            "full_passages": full_passages,
            "found_keywords": found_keywords,
            "missing_keywords": missing_keywords,
            "lost_by_truncation": lost_by_truncation,
        })

    return results


def main():
    print("TRUNCATION HYPOTHESIS TEST")
    print("Comparing support_probability with truncated vs full passages\n")

    # Test with truncation (normal API)
    trunc_results = test_with_truncation()

    # Test with full passages (direct Pinecone)
    full_results = test_with_full_passages()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print("\nWith truncation (500 chars):")
    for r in trunc_results:
        print(f"  {r['id']}: support_probability={r['support_probability']}, status={r['status']}")

    print("\nWith full passages:")
    for r in full_results:
        print(f"  {r['id']}: keywords found={r['found_keywords']}, lost_by_truncation={r['lost_by_truncation']}")

    # Determine if truncation is the cause
    zero_support = [r for r in trunc_results if r["support_probability"] == 0.0]
    keywords_in_full = [r for r in full_results if r["found_keywords"]]
    keywords_lost = [r for r in full_results if r["lost_by_truncation"]]

    print("\nConclusion:")
    if zero_support and keywords_in_full:
        print(f"  {len(zero_support)} questions have support_probability=0.0")
        print(f"  {len(keywords_in_full)} questions have keywords in full passages")
        if keywords_lost:
            print(f"  {len(keywords_lost)} questions lose keywords due to truncation")
            print("  → TRUNCATION IS LIKELY CAUSING ZERO SUPPORT")
        else:
            print("  Keywords survive truncation")
            print("  → Truncation may not be the primary cause")
    else:
        print("  No clear pattern - further investigation needed")


if __name__ == "__main__":
    main()
