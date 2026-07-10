import json

from ...state import PipelineState
from ...shared import (
    PRODUCTS,
    _run_with_server_tools,
    _extract_fetched_urls,
    _final_text,
    _clean_draft_text,
    _pick_style_reference_urls,
    _write_output,
)

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
- Near the end, a natural, non-pushy sentence or two that connects what the article covered to \
the specific Broono product you're given, written as a markdown link using its exact name and \
URL, e.g. "a daily [Broono Calm](https://www.broono.pet/products/calm) chew". Make the \
connection specific to this article's topic, not a generic tack-on.

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

Use only the exact product name and URL given to you for the link. Do not invent a price, don't \
link to a different Broono product, and don't make up a different URL.

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
    product = PRODUCTS.get(brief.get("tied_product", ""), {})

    user_content = (
        f"Brief:\n{json.dumps(brief, indent=2)}\n\n"
        f"Tied product (use this exact name and URL for the product link):\n"
        f"{json.dumps(product, indent=2)}\n\n"
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

    _write_output("draft", "latest.md", text)

    return {
        **state,
        "draft_content": text,
        "draft_references": _extract_fetched_urls(response),
        "revision_notes": None,
        "status": "drafting",
    }
