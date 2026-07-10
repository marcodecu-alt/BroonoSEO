# Propose agent

Second node in the pipeline (shown as "Simone" on the marketing "how it works" page at
`apps/web/src/lib/agents.ts` — naming only, not relevant to runtime behavior).

## Role

Picks the single strongest candidate out of the research agent's shortlist and turns it into a
structured brief (title, target keyword, angle, tied product). This brief is the green light
everything downstream (draft, review) builds on. Runs after `research_node`, before `draft_node`.

## Key file

`node.py` — `propose_node`, `PROPOSE_SYSTEM_PROMPT`, `PROPOSE_OUTPUT_SCHEMA`.

## Depends on

`_final_text`, `_write_output` (from `../../shared.py`). No server tools, no existing-articles
check — that already happened in the research step.

## Invariants — do not change these without understanding why they exist

- `tied_product` must be exactly one of the 4 keys in `shared.PRODUCTS`
  (`essential` / `move` / `calm` / `prebiotic`) — enforced today via `PROPOSE_OUTPUT_SCHEMA`'s
  `enum`. If a 5th product is ever added to `shared.PRODUCTS`, the schema's `enum` and this
  file's system prompt product list must be updated together, or they will silently drift (the
  schema enum, not the product dict, is what the model call actually respects).
- Pure reasoning, no tools. If you're tempted to add a tool call here, first confirm it's actually
  needed — the design intent is that research already gathered all the external evidence, and
  propose just picks and shapes it.

See `MEMORY.md` in this folder for accumulated learnings, prompt-tuning history, and calibration
notes for this agent specifically.
