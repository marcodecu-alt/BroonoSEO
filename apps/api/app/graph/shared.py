import re
from pathlib import Path
from urllib.parse import urlparse

from ..claude_client import client, MODEL
from ..supabase_client import supabase

AGENTS_DIR = Path(__file__).resolve().parent / "agents"

# Broono's real, complete product catalog (broono.pet/collections/all has exactly
# these 3, verified directly against the live site). Kept as a code-level lookup,
# not something either agent has to guess or fetch, so the product link in every
# article is always accurate.
PRODUCTS = {
    "essential": {
        "name": "Essential",
        "url": "https://www.broono.pet/products/essential",
        "description": "Daily foundational soft chew with antioxidants and B vitamins, "
        "supports immune function, energy balance, and general healthspan.",
        "topic_keywords": ["immune", "antioxidant", "energy", "general health", "wellness", "senior"],
    },
    "move": {
        "name": "Move",
        "url": "https://www.broono.pet/products/move",
        "description": "Joint care for active and ageing dogs, supports joint comfort, "
        "flexible movement, and cartilage care.",
        "topic_keywords": ["joint", "mobility", "stiff", "cartilage"],
    },
    "calm": {
        "name": "Calm",
        "url": "https://www.broono.pet/products/calm",
        "description": "Soft chews with adaptogens and magnesium, supports calmer "
        "behaviour, relaxed mood, and anxiety support without drowsiness.",
        "topic_keywords": ["calm", "anxiety", "relax", "magnesium", "theanine"],
    },
    "prebiotic": {
        "name": "Prebiotic",
        "url": "https://www.broono.pet/products/prebiotic",
        "description": "Soft chews that nourish beneficial gut bacteria, supports "
        "digestion, healthy skin, and immune function.",
        "topic_keywords": ["gut", "digest", "skin", "immune", "prebiotic"],
    },
}


def _domain(url: str) -> str:
    return urlparse(url).netloc.removeprefix("www.")


def _extract_search_trail(response) -> list[dict]:
    """Pull out each web_search call Nicola made and which domains it returned,
    so the Timeline can show her actual research process, not just her
    conclusions."""
    queries_by_id = {}
    for block in response.content:
        if block.type == "server_tool_use" and block.name == "web_search":
            queries_by_id[block.id] = block.input.get("query", "")

    trail = []
    for block in response.content:
        if block.type != "web_search_tool_result":
            continue
        query = queries_by_id.get(block.tool_use_id, "")
        results = block.content if isinstance(block.content, list) else []
        sources = sorted({_domain(r.url) for r in results if getattr(r, "url", None)})
        trail.append({"query": query, "sources": sources})
    return trail


def _extract_fetched_urls(response) -> list[str]:
    """Which URL(s) Celeste actually fetched for style reference."""
    urls = []
    for block in response.content:
        if block.type == "server_tool_use" and block.name == "web_fetch":
            url = block.input.get("url")
            if url:
                urls.append(url)
    return urls


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

    keywords = PRODUCTS.get(tied_product, {}).get("topic_keywords", [])
    matches = [
        a for a in articles
        if any(k in (a.get("summary") or "").lower() for k in keywords)
    ]

    chosen = (matches or articles)[:n]
    return [a["url"] for a in chosen]


def _write_output(agent: str, filename: str, content: str) -> None:
    """Best-effort debug dump to agents/<agent>/OUTPUT/<filename> for quick human
    inspection. Supabase remains the source of truth; this is disposable and
    silently no-ops on failure (e.g. read-only filesystem in some deploy
    environments) so it can never break a pipeline run."""
    try:
        out_dir = AGENTS_DIR / agent / "OUTPUT"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / filename).write_text(content, encoding="utf-8")
    except OSError:
        pass
