import json

from ....claude_client import client, MODEL
from ...state import PipelineState
from ...shared import _final_text, _write_output

PROPOSE_SYSTEM_PROMPT = """You are the proposal agent for Broono, a dog supplement DTC brand.

You'll be given a shortlist of research candidates, each with a topic, target keyword, and \
rationale. Select the single strongest candidate, the one with the clearest search demand and \
the best content gap, and turn it into a concrete content brief.

Broono sells exactly 4 products. Pick whichever one genuinely fits the candidate's topic, don't \
force a fit if none really do, pick the closest one:
- essential: daily foundational soft chew with antioxidants and B vitamins, supports immune \
function, energy balance, and general healthspan
- move: joint care for active/ageing dogs, joint comfort, flexible movement, cartilage care
- calm: soft chews with adaptogens + magnesium, calmer behaviour, relaxed mood, anxiety support
- prebiotic: soft chews that nourish gut bacteria, supports digestion, healthy skin, and immune \
function

Output:
- title: a compelling working title in Broono's blog voice (plain, helpful, not clickbait)
- target_keyword: the primary SEO keyword to write for
- angle: one or two sentences on the specific entry point/angle the article will take
- tied_product: exactly one of "essential", "move", "calm", or "prebiotic", whichever genuinely \
fits the topic"""

PROPOSE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "target_keyword": {"type": "string"},
        "angle": {"type": "string"},
        "tied_product": {"type": "string", "enum": ["essential", "move", "calm", "prebiotic"]},
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

    _write_output("propose", "latest.json", json.dumps(brief, indent=2))

    return {
        **state,
        "brief": brief,
        "status": "proposed",
    }
