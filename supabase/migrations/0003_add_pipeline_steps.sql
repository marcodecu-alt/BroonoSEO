-- Captures research_node and propose_node output, which today is used
-- transiently inside the graph run and then discarded. draft_node and
-- review_node output are already captured in article_versions and
-- review_notes respectively, so this table only needs to cover the gap.

create table pipeline_steps (
  id uuid primary key default gen_random_uuid(),
  article_id uuid not null references articles (id) on delete cascade,
  agent text not null check (agent in ('research_node', 'propose_node')),
  output_json jsonb not null,
  created_at timestamptz not null default now()
);

create index on pipeline_steps (article_id);

alter table pipeline_steps enable row level security;
