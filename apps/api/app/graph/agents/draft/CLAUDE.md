# Draft agent

Third node in the pipeline (shown as "Celeste" on the marketing "how it works" page at
`apps/web/src/lib/agents.ts` — naming only, not relevant to runtime behavior).

## Role

Writes the full 900-1,200 word Markdown article from the propose agent's brief, fetching 1-2
existing Broono articles first to match voice/structure. Runs after `propose_node`, before
`review_node`. Also the re-entry point for `build_resume_graph()` when a human leaves a comment
on a version awaiting approval.

## Key file

`node.py` — `draft_node`, `DRAFT_SYSTEM_PROMPT`.

## Depends on (from `../../shared.py`)

`PRODUCTS`, `_run_with_server_tools`, `_extract_fetched_urls`, `_final_text`,
`_clean_draft_text`, `_pick_style_reference_urls`, `_write_output`.

## Invariants — do not change these without understanding why they exist

- Must never invent a product URL, price, or name. Always use the exact
  `PRODUCTS[tied_product]` dict passed into the prompt verbatim. This is explicit in
  `DRAFT_SYSTEM_PROMPT` ("Use only the exact product name and URL given to you... don't make up
  a different URL") and is a hard brand/legal-adjacent constraint, not a style preference.
- Image briefs must never describe real product packaging or labels — there's no real product
  photography to match against, so a generated image of fake packaging is unusable.
- `_clean_draft_text` strips code fences and pre-H1 narration text. This is a known, recurring
  model habit (Haiku), not incidental — don't delete this safety net even if a spot check makes
  it look unnecessary.
- `web_fetch` is called with `allowed_callers: ["direct"]`, same reason as the research agent's
  `web_search`: Haiku 4.5 doesn't support the programmatic-tool-calling mode dynamic filtering
  defaults to.
- Must handle the `revision_notes` / previous-draft branch (`state.get("revision_notes")`,
  `state.get("draft_content")`) — this is exactly what `build_resume_graph()` re-enters at after
  a human comment, and treats those notes as required changes, not suggestions.

See `MEMORY.md` in this folder for accumulated learnings, prompt-tuning history, and calibration
notes for this agent specifically.
