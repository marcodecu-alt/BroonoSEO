# Review agent

Fourth and final node in the pipeline (shown as "Sofia" on the marketing "how it works" page at
`apps/web/src/lib/agents.ts` — naming only, not relevant to runtime behavior).

## Role

Checks the draft against a fixed 4-item checklist (health claims, tone, SEO basics,
duplication), then always hands off to the human for approval. Runs after `draft_node`, and is
also the exit point of both `build_graph()` and `build_resume_graph()`.

## Key file

`node.py` — `review_node`, `REVIEW_SYSTEM_PROMPT`, `REVIEW_OUTPUT_SCHEMA`.

## Depends on

`_final_text`, `_existing_articles_summary`, `_write_output` (from `../../shared.py`).

## Invariants — do not change these without understanding why they exist

- **`review_node` must never loop back to `draft_node` on its own.** `graph.py` wires
  `review_node → END` unconditionally in both graphs. This was a deliberate fix after a real run
  hit LangGraph's `recursion_limit` (25) without converging, burning API calls on a topic the
  checklist kept rejecting. Only a human comment triggers another draft → review pass, via
  `build_resume_graph()`. Do not reintroduce a conditional edge from `review_node` back to
  `draft_node` without discussing this explicitly first, it would reverse a fix for a real
  production incident.
- `health_claims` is advisory-only and is force-set to `passed: True` in code after the model
  call, regardless of what the model itself returns. This is intentional, a Haiku judgment call
  on medical claims should never silently block an article; the note is still surfaced to the
  human. Don't "fix" this by trusting the model's own `passed` value for that item.
- `passed` is the AND of all 4 checklist items (with `health_claims` forced true as above).

See `MEMORY.md` in this folder for accumulated learnings, prompt-tuning history, and calibration
notes for this agent specifically.
