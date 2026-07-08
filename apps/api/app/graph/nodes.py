import json
import re

from ..claude_client import client, MODEL
from ..supabase_client import supabase
from .state import PipelineState


def _run_with_server_tools(system_prompt, user_content, tools, output_schema=None, max_tokens=16000):
    """Server-side tools (web_search, web_fetch) resolve within one call, but can
    pause_turn on long tool use. Resend to let Claude continue until it's done."""
    kwargs = dict(
        model=MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        tools=tools,
        messages=[{"role": "user", "content": user_content}],
    )
    if output_schema:
        kwargs["output_config"] = {"format": {"type": "json_schema", "schema": output_schema}}

    response = client.messages.create(**kwargs)

    while response.stop_reason == "pause_turn":
        kwargs["messages"] = [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": response.content},
        ]
        response = client.messages.create(**kwargs)

    return response


def _final_text(response) -> str:
    """When tools are involved, Claude may emit narration text blocks before/between
    tool calls. The real answer is the last text block, not the first."""
    text_blocks = [b for b in response.content if b.type == "text"]
    return text_blocks[-1].text


def _clean_draft_text(text: str) -> str:
    """Safety net for two habits the model has despite being told not to: wrapping
    the article in a ```markdown fence, and adding a narration sentence before the
    H1 (e.g. "I'll write the article now...")."""
    text = text.strip()
    fence_match = re.search(r"```(?:markdown)?\n(.*)\n```\s*$", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    h1_match = re.search(r"^# .+$", text, re.MULTILINE)
    if h1_match and h1_match.start() > 0:
        text = text[h1_match.start():].strip()
    return text


def _existing_articles() -> list[dict]:
    resp = supabase.table("existing_content_index").select(
        "url, title, target_keyword, summary"
    ).execute()
    return resp.data


def _existing_articles_summary() -> str:
    articles = _existing_articles()
    if not articles:
        return "(none indexed yet)"
    return "\n".join(
        f"- {row['title']} (keyword: {row.get('target_keyword') or 'n/a'}) — {row.get('summary') or ''}"
        for row in articles
    )


def _pick_style_reference_urls(tied_product: str, n: int = 1) -> list[str]:
    """Pick n existing articles most related to the tied product for style reference,
    falling back to the first n indexed articles if nothing matches."""
    articles = _existing_articles()
    if not articles:
        return []

    keywords = tied_product.lower().split("/")
    matches = [
        a for a in articles
        if any(k.strip() and k.strip() in (a.get("summary") or "").lower() for k in keywords)
    ]

    chosen = (matches or articles)[:n]
    return [a["url"] for a in chosen]


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

    text = _final_text(response)
    brief = json.loads(text)

    return {
        **state,
        "brief": brief,
        "status": "proposed",
    }


DRAFT_SYSTEM_PROMPT = """You are the draft agent for Broono, a dog supplement DTC brand \
(https://www.broono.pet/blogs/dog-health-articles).

You'll be given a content brief and 1-2 URLs of Broono's existing published articles. Use the \
web_fetch tool to read those reference articles first, to match Broono's voice, structure, and \
formatting conventions (they tend to be practical, warm, non-alarmist, and end with a natural \
tie-in to a Broono product without being pushy).

Write the complete article in Markdown:
- Target length: 900-1,200 words. Be direct and comprehensive, not padded, cut anything that \
doesn't serve the reader's actual question.
- Answer the core question in the first 2-3 sentences, before any scene-setting. Someone \
searching a symptom wants the answer fast.
- Open with a specific, concrete, recognizable scenario the reader will immediately recognize \
themselves in, never a generic statement like "As a dog owner, you may have noticed...".
- A single H1 title in plain language, centered on the reader's exact question or concern, with \
the target keyword near the front. No clickbait, no generic "Benefits of X" framing.
- A one-sentence meta description near the top, labeled "Meta description:"
- Proper H2/H3 structure
- A short FAQ section near the end (2-3 Q&As, or up to 4 only if the word budget allows) if \
relevant to the topic, matching the pattern in Broono's existing content
- A natural, non-pushy mention of the tied Broono product category near the end

Include image briefs so a human can generate or source real images later: one immediately after \
the meta description (the hero image), and optionally one more at a natural point in the body if \
it meaningfully helps illustrate a specific section (not required for every section, don't force \
it). Format each one as its own line, exactly:

> **Image brief:** <description>

Each description must be a self-contained brief usable directly as a prompt for an AI image tool \
or a brief for a photographer: specific subject (matched to this article's actual topic, not a \
generic "a dog"), setting, mood, and a natural editorial photography style. Never describe \
specific product packaging, labels, or branding, we don't have real product photography to match \
against, so a generated image of fake packaging would be unusable. No text overlays in the \
description, that's a separate design step.

Do not include any health/medical claims that aren't well established and safe to state for a \
supplement brand (e.g. don't claim to cure, treat, or diagnose disease; recommend vets for \
anything that sounds like a medical emergency or persistent symptom).

Refer to the tied product only by its general category from the brief (e.g. "a joint support \
supplement" or "a daily joint chew"). Do not invent a specific product name, price, or URL, we \
don't have Broono's exact product catalog wired in yet.

If revision notes are provided, treat them as required changes to the previous draft, not \
suggestions.

Your final response message must contain nothing but the raw article Markdown. Do not wrap it in \
a code fence. Do not begin with a sentence about your plan or process (e.g. "I'll write the \
article now" or "Here's the article"), the very first characters of your response must be the \
H1 heading itself, and nothing should follow the article's last line."""


def draft_node(state: PipelineState) -> PipelineState:
    """Write the full article from the brief, using existing articles as style reference."""
    brief = state.get("brief", {})
    revision_notes = state.get("revision_notes")
    reference_urls = _pick_style_reference_urls(brief.get("tied_product", ""))

    user_content = (
        f"Brief:\n{json.dumps(brief, indent=2)}\n\n"
        f"Style reference articles:\n" + "\n".join(reference_urls or ["(none indexed yet)"])
    )
    if revision_notes:
        user_content += f"\n\nRevision notes (required changes to the previous draft):\n{revision_notes}"
        user_content += f"\n\nPrevious draft:\n{state.get('draft_content', '')}"

    response = _run_with_server_tools(
        DRAFT_SYSTEM_PROMPT,
        user_content,
        tools=[
            {
                "type": "web_fetch_20260209",
                "name": "web_fetch",
                "max_content_tokens": 4000,
                # Same allowed_callers fix as web_search: Haiku 4.5 doesn't support
                # the programmatic-tool-calling mode dynamic filtering defaults to.
                "allowed_callers": ["direct"],
            }
        ],
    )

    text = _clean_draft_text(_final_text(response))

    return {
        **state,
        "draft_content": text,
        "revision_notes": None,
        "status": "drafting",
    }


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

    # Review runs once and never blocks: it always hands off to the human with
    # its findings attached, rather than looping back to draft_node on its own.
    # A run that can't converge would otherwise burn API calls up to
    # recursion_limit before failing outright. The human decides whether a
    # failed item needs a redraft (via a comment) or is fine to publish as-is.
    return {
        **state,
        "review_checklist": checklist,
        "review_passed": passed,
        "revision_notes": None if passed else result.get("revision_notes"),
        "status": "awaiting_approval",
    }
