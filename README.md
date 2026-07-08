# Broono SEO Content Pipeline

A multi-user web app that produces SEO-focused blog articles for [Broono](https://www.broono.pet/blogs/dog-health-articles) (a dog supplement DTC brand) via an automated agent pipeline: research → propose → draft → review, with a review→draft revision loop, gated by human approval before export.

Broono's blog has solid technical SEO but weak cadence (~12 articles since 2023) and narrow topic coverage (mostly ingredient-led "benefits of X" articles, missing the larger volume of symptom/problem-led search terms dog owners actually use, e.g. "why is my dog limping" vs. "benefits of magnesium for dogs"). The pipeline is built to close that gap.

## Non-goals for v1

- No auto-publishing to Shopify. Output is a formatted document for manual upload.
- No paid SEO API integration (Ahrefs/Semrush/DataForSEO). Research is free/search-based only.
- No self-serve signup. Accounts are created directly by the project owner.
- No fan-out/parallel agent execution. Sequential pipeline, one conditional loop (review → draft).

## Architecture

- **Frontend** (`apps/web`): Next.js, deployed on Vercel.
- **Auth + DB**: Supabase (email/password auth, Postgres).
- **Backend / orchestration** (`apps/api`): FastAPI running LangGraph as a library (not the hosted platform).
- **LLM**: Claude API for all agent calls.
- **Research**: free/search-based only.

## Structure

```
apps/
  web/    Next.js frontend (login, dashboard, article detail)
    src/
      app/login, app/dashboard, app/articles/[id]
      lib/supabase.ts   Supabase auth client
      lib/api.ts         typed fetch client for the FastAPI backend
  api/    FastAPI backend + LangGraph pipeline
    app/
      main.py            FastAPI app + article endpoints
      pipeline_runner.py  runs the graph as a background task, persists to Supabase
      supabase_client.py, claude_client.py
      graph/
        state.py          Pipeline state shape
        nodes.py           research / propose / draft / review nodes
        graph.py           LangGraph wiring: single-pass graph + resume-from-draft graph
    scripts/
      seed_content_index.py  one-time scrape of Broono's published articles
      run_pipeline.py         run one topic through the full graph via CLI
supabase/migrations/0001_init.sql
```

## Pipeline

```
research_node → propose_node → draft_node → review_node → awaiting_human_approval
```

Single pass, no auto-retry loop. `review_node` runs once and always hands the
article to the human with its checklist findings attached, whether or not
everything passed, it never loops back to `draft_node` on its own. This was a
deliberate change after a real run hit LangGraph's recursion limit (25 rounds)
without ever converging, burning API calls on a topic the review checklist
kept rejecting. The human is the actual gate now: reading the checklist notes
and, if a redraft is genuinely needed, leaving a comment to trigger exactly
one more draft → review pass.

## Review checklist (review_node)

1. No unsupported health/medical claims (highest priority, supplement brand making animal health claims)
2. Brand tone/voice consistency
3. On-page SEO basics (headers, natural keyword use, meta description)
4. No duplication against existing published content

## Data model (Supabase Postgres)

- `users` — id, email, role (`owner` | `reviewer`)
- `articles` — id, status, brief_json, timestamps
- `article_versions` — full history of every draft/revision, never overwritten
- `review_notes` — checklist_json, passed
- `comments` — human feedback attached to a version, fed back into the draft agent
- `existing_content_index` — cached index of Broono's published articles, used to avoid duplicate topics

## API (FastAPI, `apps/api`)

- `POST /articles/start` — kick off a new pipeline run (optional topic seed)
- `GET /articles` — list all articles
- `GET /articles/{id}` — status, latest draft, review notes, comment history
- `POST /articles/{id}/approve` — finalize, triggers export
- `POST /articles/{id}/comment` — attach comment, re-triggers draft→review loop
- `GET /articles/{id}/export` — formatted document for the approved version

## Dev setup

### Frontend

```
cd apps/web
npm install
npm run dev        # http://localhost:3000
```

### Backend

```
cd apps/api
python -m venv venv
./venv/Scripts/pip install -r requirements.txt   # Windows
source venv/bin/activate && pip install -r requirements.txt  # macOS/Linux
cp .env.example .env   # fill in ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
./venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

## Deployment

Repo: https://github.com/marcodecu-alt/BroonoSEO

**Backend (`apps/api`) → Railway.** Needs a host that supports a long-running process,
not a serverless function, because `POST /articles/start` kicks off a background task
(web search, several Claude calls, can run 1-3+ minutes) that keeps running after the
HTTP response is sent. Vercel/serverless functions get killed once the response returns,
so the frontend can't host this part.

1. Connect the GitHub repo in Railway, set the service's root directory to `apps/api`
2. Railway picks up `Procfile` (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`) and
   `.python-version` automatically via Nixpacks
3. Set env vars: `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`,
   `ALLOWED_ORIGINS` (the deployed Vercel URL, comma-separated if more than one)
4. Note the public URL Railway gives the service, needed for the frontend's
   `NEXT_PUBLIC_API_URL` below

**Frontend (`apps/web`) → Vercel.**

1. Connect the same GitHub repo in Vercel, set the project's root directory to `apps/web`
2. Set env vars: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` (same values
   as local `.env.local`), `NEXT_PUBLIC_API_URL` (the Railway URL from above)
3. Once deployed, take the Vercel URL and set it as `ALLOWED_ORIGINS` on Railway (step 3
   above), redeploy the backend so CORS allows the production frontend

## Status

End-to-end functional. Supabase schema, auth, and all 4 LangGraph nodes are wired to real Claude API calls (web search for research, web fetch for style reference in drafting). The full pipeline, the review→draft loop, human comments, approval, and export have all been verified against the live API/Supabase, including a real run through the frontend in a browser (login → dashboard → article detail → approve → export).

Not yet done: calibrating the review checklist against more real topics (currently only run against a handful), and a second `reviewer` account (only the `owner` account exists so far, add via the same admin-API flow used for the first).

## Build order

1. Supabase schema + auth, create owner + reviewer accounts ✅ (owner account created, reviewer pending)
2. FastAPI skeleton, confirm Next.js ↔ FastAPI round trip ✅
3. Build each LangGraph node in isolation with real Claude API calls ✅
4. Wire the full graph incl. review→draft loop, run one topic through end to end via CLI ✅
5. Build the Next.js dashboard and article detail view ✅
6. Wire approve/comment actions from frontend into the backend API ✅
7. Build the export-to-document step ✅
8. Run against 2-3 real topics, calibrate the review agent's checklist (ongoing)
