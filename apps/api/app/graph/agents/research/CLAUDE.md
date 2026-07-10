# Research agent

First node in the pipeline (shown as "Nicola" on the marketing "how it works" page at
`apps/web/src/lib/agents.ts` — naming only, not relevant to runtime behavior).

## Role

Finds 2-3 symptom/problem-led topic candidates with real search demand (e.g. "why is my dog
limping" rather than "benefits of magnesium for dogs"), cross-checked against
`existing_content_index` so Broono's blog never gets a duplicate topic. Runs first in
`graph.py`'s `build_graph()`; hands its output to the propose agent.

## Key file

`node.py` — `research_node`, `RESEARCH_SYSTEM_PROMPT`, `RESEARCH_OUTPUT_SCHEMA`.

## Depends on (from `../../shared.py`)

`_run_with_server_tools`, `_extract_search_trail`, `_final_text`, `_existing_articles_summary`,
`_write_output`.

## Invariants — do not change these without understanding why they exist

- Must always cross-check candidates against `existing_content_index` and reject duplicates.
  This is the entire reason a research step exists ahead of an ingredient-led blog with narrow
  topic coverage — skipping this defeats the point of the agent.
- `web_search` is called with `allowed_callers: ["direct"]`. Dynamic filtering (the tool's
  default) requires a model tier that supports programmatic tool calling, which Haiku 4.5 does
  not. Don't remove this or swap the model without re-checking that constraint.
- Output must conform to `RESEARCH_OUTPUT_SCHEMA` (2-3 candidates, each with `topic` /
  `target_keyword` / `rationale`) — `propose_node` consumes this shape directly.

See `MEMORY.md` in this folder for accumulated learnings, prompt-tuning history, and calibration
notes for this agent specifically.
