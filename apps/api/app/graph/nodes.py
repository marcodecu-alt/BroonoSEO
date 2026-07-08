import json

from ..claude_client import client, MODEL
from ..supabase_client import supabase
from .state import PipelineState

RESEARCH_SYSTEM_PROMPT = """You are the research agent for Broono, a dog supplement DTC brand \
(https://www.broono.pet/blogs/dog-health-articles).

Broono's existing blog is ingredient-led ("benefits of magnesium for dogs") but dog owners \
mostly search symptom- and problem-led queries ("why is my dog limping"). Your job is to find \
2-3 symptom/problem-led topic candidates with real search demand that Broono has not already \
covered, and that plausibly tie back to one of Broono's supplement products (joint, digestive, \
skin/coat, calming, immune support, etc).

Use web search to find what dog owners actually search for: forums, "people also ask"-style \
questions, autocomplete-style phrasing. Do not propose another ingredient-benefits article.

Cross-check every candidate against the "existing articles" list you're given. Reject a \
candidate if it duplicates the topic or target keyword of an existing article.

Return each candidate with: the working topic, the target keyword, and a short rationale \
covering apparent search demand, the content gap it fills, and why it's distinct from existing \
content."""

RESEARCH_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "target_keyword": {"type": "string"},
                    "rationale": {"type": "string"},
                },
                "required": ["topic", "target_keyword", "rationale"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["candidates"],
    "additionalProperties": False,
}


def _existing_articles_summary() -> str:
    resp = supabase.table("existing_content_index").select(
        "title, target_keyword, summary"
    ).execute()
    if not resp.data:
        return "(none indexed yet)"
    return "\n".join(
        f"- {row['title']} (keyword: {row.get('target_keyword') or 'n/a'}) — {row.get('summary') or ''}"
        for row in resp.data
    )


def _run_until_done(user_content: str):
    """Server-side tools (web_search) resolve within one call, but can pause_turn on
    long searches. Resend to let Claude continue until it produces a final answer."""
    messages = [{"role": "user", "content": user_content}]
    response = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=RESEARCH_SYSTEM_PROMPT,
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        output_config={"format": {"type": "json_schema", "schema": RESEARCH_OUTPUT_SCHEMA}},
        messages=messages,
    )

    while response.stop_reason == "pause_turn":
        messages = [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": response.content},
        ]
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=RESEARCH_SYSTEM_PROMPT,
            tools=[{"type": "web_search_20260209", "name": "web_search"}],
            output_config={"format": {"type": "json_schema", "schema": RESEARCH_OUTPUT_SCHEMA}},
            messages=messages,
        )

    return response


def research_node(state: PipelineState) -> PipelineState:
    """Find symptom/problem-led topic candidates, cross-checked against existing_content_index."""
    topic_seed = state.get("topic_seed")
    existing = _existing_articles_summary()

    user_content = (
        f"Existing Broono articles (do not duplicate):\n{existing}\n\n"
        + (f"Topic seed to explore: {topic_seed}" if topic_seed else "Find the next best topic.")
    )

    response = _run_until_done(user_content)

    text_block = next(b for b in response.content if b.type == "text")
    candidates = json.loads(text_block.text)["candidates"]

    return {
        **state,
        "research_candidates": candidates,
        "status": "researching",
    }


PROPOSE_SYSTEM_PROMPT = """You are the proposal agent for Broono, a dog supplement DTC brand.

You'll be given a shortlist of research candidates, each with a topic, target keyword, and \
rationale. Select the single strongest candidate, the one with the clearest search demand and \
the best content gap, and turn it into a concrete content brief.

Output:
- title: a compelling working title in Broono's blog voice (plain, helpful, not clickbait)
- target_keyword: the primary SEO keyword to write for
- angle: one or two sentences on the specific entry point/angle the article will take
- tied_product: which Broono supplement category this ties back to (e.g. joint/mobility, \
digestive, skin/coat, calming, immune support), inferred from the candidate's rationale"""

PROPOSE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "target_keyword": {"type": "string"},
        "angle": {"type": "string"},
        "tied_product": {"type": "string"},
    },
    "required": ["title", "target_keyword", "angle", "tied_product"],
    "additionalProperties": False,
}


def propose_node(state: PipelineState) -> PipelineState:
    """Pick the strongest research candidate and build a structured brief."""
    candidates = state.get("research_candidates", [])

    response = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=PROPOSE_SYSTEM_PROMPT,
        output_config={"format": {"type": "json_schema", "schema": PROPOSE_OUTPUT_SCHEMA}},
        messages=[
            {
                "role": "user",
                "content": "Research candidates:\n" + json.dumps(candidates, indent=2),
            }
        ],
    )

    text_block = next(b for b in response.content if b.type == "text")
    brief = json.loads(text_block.text)

    return {
        **state,
        "brief": brief,
        "status": "proposed",
    }


def draft_node(state: PipelineState) -> PipelineState:
    """Write the full article from the brief, using existing articles as style reference."""
    # TODO: draft via Claude, incorporating revision_notes if present
    return {
        **state,
        "draft_content": "",
        "status": "drafting",
    }


def review_node(state: PipelineState) -> PipelineState:
    """Check the draft against the fixed checklist."""
    # TODO: run checklist via Claude
    checklist = {
        "health_claims": {"passed": True, "note": ""},
        "tone": {"passed": True, "note": ""},
        "seo_basics": {"passed": True, "note": ""},
        "duplication": {"passed": True, "note": ""},
    }
    passed = all(item["passed"] for item in checklist.values())
    return {
        **state,
        "review_checklist": checklist,
        "review_passed": passed,
        "status": "awaiting_approval" if passed else "drafting",
    }


def review_router(state: PipelineState) -> str:
    return "awaiting_human_approval" if state.get("review_passed") else "draft_node"
