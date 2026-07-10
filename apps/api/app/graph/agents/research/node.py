import json

from ...state import PipelineState
from ...shared import _run_with_server_tools, _extract_search_trail, _final_text, _existing_articles_summary, _write_output

RESEARCH_SYSTEM_PROMPT = """You are the research agent for Broono, a dog supplement DTC brand \
(https://www.broono.pet/blogs/dog-health-articles).

Broono's existing blog is ingredient-led ("benefits of magnesium for dogs") but dog owners \
mostly search symptom- and problem-led queries ("why is my dog limping"). Your job is to find \
2-3 symptom/problem-led topic candidates with real search demand that Broono has not already \
covered, and that plausibly tie back to one of Broono's supplement products (joint, digestive, \
skin/coat, calming, immune support, etc).

Use web search to check two kinds of sources for every candidate you consider:
1. Forums and communities (e.g. Reddit) where owners describe the problem in their own words. \
This is how you catch the real phrasing and emotional framing behind a search, not the cleaned-up \
version.
2. Competitor and vet-clinic content already ranking for the topic. This is how you confirm real \
search demand actually exists, and see exactly what's already covered so you can identify the \
genuine gap rather than guessing at one.

Also check "people also ask"-style questions and autocomplete-style phrasing. Do not propose \
another ingredient-benefits article.

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


def research_node(state: PipelineState) -> PipelineState:
    """Find symptom/problem-led topic candidates, cross-checked against existing_content_index."""
    topic_seed = state.get("topic_seed")
    existing = _existing_articles_summary()

    user_content = (
        f"Existing Broono articles (do not duplicate):\n{existing}\n\n"
        + (f"Topic seed to explore: {topic_seed}" if topic_seed else "Find the next best topic.")
    )

    response = _run_with_server_tools(
        RESEARCH_SYSTEM_PROMPT,
        user_content,
        tools=[
            {
                "type": "web_search_20260209",
                "name": "web_search",
                "max_uses": 4,
                # Dynamic filtering (the default allowed_callers) requires a model tier
                # that supports programmatic tool calling; Haiku 4.5 doesn't, so call
                # web_search directly instead.
                "allowed_callers": ["direct"],
            }
        ],
        output_schema=RESEARCH_OUTPUT_SCHEMA,
    )

    text = _final_text(response)
    candidates = json.loads(text)["candidates"]

    _write_output("research", "latest.json", json.dumps(candidates, indent=2))

    return {
        **state,
        "research_candidates": candidates,
        "research_searches": _extract_search_trail(response),
        "status": "researching",
    }
