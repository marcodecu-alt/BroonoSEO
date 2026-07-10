# Broono SEO Content Pipeline

A multi-user web app that produces SEO-focused blog articles for [Broono](https://www.broono.pet/blogs/dog-health-articles)
(a dog supplement DTC brand) via an automated agent pipeline: research → propose → draft →
review, with a review → draft revision loop, gated by human approval before export.

Broono's blog has solid technical SEO but weak cadence and narrow topic coverage (mostly
ingredient-led "benefits of X" articles, missing the larger volume of symptom/problem-led search
terms dog owners actually use, e.g. "why is my dog limping" vs. "benefits of magnesium for
dogs"). The pipeline is built to close that gap.

## Non-goals for v1

- No auto-publishing to Shopify. Output is a formatted document for manual upload.
- No paid SEO API integration (Ahrefs/Semrush/DataForSEO). Research is free/search-based only.
- No self-serve signup. Accounts are created directly by the project owner.
- No fan-out/parallel agent execution. Sequential pipeline, one conditional loop (review → draft).

## Architecture

- **Frontend** (`apps/web`): Next.js, deployed on Vercel.
- **Auth + DB**: Supabase (email/password auth, Postgres).
- **Backend / orchestration** (`apps/api`): FastAPI running LangGraph as a library (not the
  hosted platform), deployed to Railway because a pipeline run is a long-running background task
  (web search, several Claude calls, can run 1-3+ minutes) that Vercel/serverless would kill.
- **LLM**: Claude API for all agent calls.
- **Research**: free/search-based only.

## Repo structure

```
apps/
  web/    Next.js frontend (login, dashboard, article detail, how-it-works)
    CLAUDE.md -> AGENTS.md   Next.js-specific coding rules, read that before editing apps/web
  api/    FastAPI backend + LangGraph pipeline
    app/
      main.py            FastAPI app + article endpoints
      pipeline_runner.py  runs the graph as a background task, persists to Supabase
      supabase_client.py, claude_client.py
      graph/
        state.py          Pipeline state shape
        graph.py           LangGraph wiring: single-pass graph + resume-from-draft graph
        shared.py          Cross-agent helpers + Broono's product catalog
        agents/
          research/        Nicola: finds topic candidates (node.py, CLAUDE.md, MEMORY.md, OUTPUT/)
          propose/         Simone: picks a candidate, builds the brief
          draft/           Celeste: writes the article
          review/          Sofia: checks the article against a fixed checklist
    scripts/
      seed_content_index.py  one-time scrape of Broono's published articles
      run_pipeline.py         run one topic through the full graph via CLI
supabase/migrations/
```

Each pipeline agent's implementation lives in its own folder under
`apps/api/app/graph/agents/<name>/`, with its own `CLAUDE.md` (role, dependencies, hard
invariants) and `MEMORY.md` (learnings log for that agent specifically). Read the relevant one
before editing that agent's `node.py`.

## The pipeline's one deliberate loop

```
research_node → propose_node → draft_node → review_node → awaiting_human_approval
```

Single pass, no auto-retry loop. `review_node` runs once and always hands the article to the
human with its checklist findings attached, whether or not everything passed, it never loops
back to `draft_node` on its own. This was a deliberate change after a real run hit LangGraph's
recursion limit (25 rounds) without ever converging, burning API calls on a topic the review
checklist kept rejecting. The human is the actual gate now: reading the checklist notes and, if a
redraft is genuinely needed, leaving a comment to trigger exactly one more draft → review pass.
This is the single most important piece of tribal knowledge in this repo, see
`apps/api/app/graph/agents/review/CLAUDE.md` for the full detail before touching that node.

## Data model (Supabase Postgres)

- `users` — id, email, role (`owner` | `reviewer`)
- `articles` — id, status, brief_json, timestamps
- `article_versions` — full history of every draft/revision, never overwritten
- `review_notes` — checklist_json, passed
- `comments` — human feedback attached to a version, fed back into the draft agent
- `existing_content_index` — cached index of Broono's published articles, used to avoid
  duplicate topics

Each agent also writes its latest output to a local `OUTPUT/latest.*` file for quick inspection
(`apps/api/app/graph/agents/<name>/OUTPUT/`), but Supabase remains the actual source of truth and
full history.

## Status

End-to-end functional. Supabase schema, auth, and all 4 LangGraph nodes are wired to real Claude
API calls. The full pipeline, the review→draft loop, human comments, approval, and export have
all been verified against the live API/Supabase.

Not yet done: calibrating the review checklist against more real topics, and a second `reviewer`
account.

## Keeping memory current

Keep `MEMORY.md` (this folder) updated with cross-cutting learnings, architectural decisions,
and user feedback that don't belong to one specific agent. Agent-specific learnings go in that
agent's own `MEMORY.md` under `apps/api/app/graph/agents/<name>/` instead.
