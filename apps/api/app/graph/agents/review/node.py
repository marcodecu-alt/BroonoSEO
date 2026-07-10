import json

from ....claude_client import client, MODEL
from ...state import PipelineState
from ...shared import _final_text, _existing_articles_summary, _write_output

REVIEW_SYSTEM_PROMPT = """You are the review agent for Broono, a dog supplement DTC brand. You \
check a drafted article against a fixed checklist before it goes to a human for approval.

Checklist:
1. health_claims: Note any unsupported health/medical claims (e.g. claiming to cure, treat, \
prevent, or diagnose a disease, or stating a benefit as guaranteed medical fact). This item is \
advisory only, it never fails the review. Always set passed=true for it regardless of what you \
find, but write a clear, specific note describing any claims worth a human's attention before \
publishing. If you see nothing concerning, say so briefly.
2. tone: Brand tone/voice consistency, practical, warm, non-alarmist, matches the existing \
Broono articles provided for reference.
3. seo_basics: On-page SEO basics, H1 present, H2/H3 structure present, target keyword used \
naturally (not stuffed), a meta description present.
4. duplication: No duplication against existing published content, listed below. Fail if the \
draft covers substantially the same angle as an existing article.

For each item return passed (true/false) and a short note explaining the verdict. If any item \
other than health_claims fails, also return revision_notes: specific, actionable instructions \
for the draft agent to fix the failing item(s)."""

REVIEW_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "health_claims": {
            "type": "object",
            "properties": {"passed": {"type": "boolean"}, "note": {"type": "string"}},
            "required": ["passed", "note"],
            "additionalProperties": False,
        },
        "tone": {
            "type": "object",
            "properties": {"passed": {"type": "boolean"}, "note": {"type": "string"}},
            "required": ["passed", "note"],
            "additionalProperties": False,
        },
        "seo_basics": {
            "type": "object",
            "properties": {"passed": {"type": "boolean"}, "note": {"type": "string"}},
            "required": ["passed", "note"],
            "additionalProperties": False,
        },
        "duplication": {
            "type": "object",
            "properties": {"passed": {"type": "boolean"}, "note": {"type": "string"}},
            "required": ["passed", "note"],
            "additionalProperties": False,
        },
        "revision_notes": {"type": ["string", "null"]},
    },
    "required": ["health_claims", "tone", "seo_basics", "duplication", "revision_notes"],
    "additionalProperties": False,
}


def review_node(state: PipelineState) -> PipelineState:
    """Check the draft against the fixed checklist."""
    draft = state.get("draft_content", "")
    brief = state.get("brief", {})
    existing = _existing_articles_summary()

    user_content = (
        f"Brief:\n{json.dumps(brief, indent=2)}\n\n"
        f"Existing published articles (check duplication against these):\n{existing}\n\n"
        f"Draft to review:\n{draft}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=REVIEW_SYSTEM_PROMPT,
        output_config={"format": {"type": "json_schema", "schema": REVIEW_OUTPUT_SCHEMA}},
        messages=[{"role": "user", "content": user_content}],
    )

    text = _final_text(response)
    result = json.loads(text)

    checklist = {
        # health_claims is advisory only (owner's call): forced passed=true in code
        # so a Haiku judgment call can never accidentally block on it. The note is
        # still generated for the owner's own visibility before publishing.
        "health_claims": {**result["health_claims"], "passed": True},
        "tone": result["tone"],
        "seo_basics": result["seo_basics"],
        "duplication": result["duplication"],
    }
    passed = all(item["passed"] for item in checklist.values())

    revision_notes = None if passed else result.get("revision_notes")

    _write_output(
        "review",
        "latest.json",
        json.dumps({"checklist": checklist, "passed": passed, "revision_notes": revision_notes}, indent=2),
    )

    # Review runs once and never blocks: it always hands off to the human with
    # its findings attached, rather than looping back to draft_node on its own.
    # A run that can't converge would otherwise burn API calls up to
    # recursion_limit before failing outright. The human decides whether a
    # failed item needs a redraft (via a comment) or is fine to publish as-is.
    return {
        **state,
        "review_checklist": checklist,
        "review_passed": passed,
        "revision_notes": revision_notes,
        "status": "awaiting_approval",
    }
