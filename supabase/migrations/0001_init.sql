-- Broono SEO pipeline: initial schema
-- Run this in the Supabase SQL Editor (or via `supabase db push`).
--
-- Access model: the Next.js frontend only talks to Supabase Auth directly
-- (email/password login). All article/version/review/comment data goes
-- through the FastAPI backend, which uses the service_role key and so
-- bypasses RLS. RLS is enabled with no permissive policies for
-- anon/authenticated, meaning direct table access via the Supabase REST
-- API is denied for everyone except the backend's service role.

create type user_role as enum ('owner', 'reviewer');

create type article_status as enum (
  'researching',
  'proposed',
  'drafting',
  'reviewing',
  'awaiting_approval',
  'approved',
  'archived'
);

create type version_author as enum ('draft_agent', 'review_agent', 'human');

-- Mirrors auth.users for the small, fixed set of accounts the owner creates manually.
create table users (
  id uuid primary key references auth.users (id) on delete cascade,
  email text not null unique,
  role user_role not null default 'reviewer',
  created_at timestamptz not null default now()
);

create table articles (
  id uuid primary key default gen_random_uuid(),
  status article_status not null default 'researching',
  brief_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table article_versions (
  id uuid primary key default gen_random_uuid(),
  article_id uuid not null references articles (id) on delete cascade,
  version_number int not null,
  content text not null,
  created_by version_author not null,
  created_at timestamptz not null default now(),
  unique (article_id, version_number)
);

create table review_notes (
  id uuid primary key default gen_random_uuid(),
  article_id uuid not null references articles (id) on delete cascade,
  version_id uuid not null references article_versions (id) on delete cascade,
  checklist_json jsonb not null,
  passed boolean not null,
  created_at timestamptz not null default now()
);

create table comments (
  id uuid primary key default gen_random_uuid(),
  article_id uuid not null references articles (id) on delete cascade,
  version_id uuid not null references article_versions (id) on delete cascade,
  user_id uuid not null references users (id) on delete cascade,
  comment_text text not null,
  created_at timestamptz not null default now()
);

create table existing_content_index (
  id uuid primary key default gen_random_uuid(),
  url text not null unique,
  title text not null,
  target_keyword text,
  summary text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index on articles (status);
create index on article_versions (article_id);
create index on review_notes (article_id);
create index on comments (article_id);

create function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger articles_set_updated_at
  before update on articles
  for each row execute function set_updated_at();

create trigger existing_content_index_set_updated_at
  before update on existing_content_index
  for each row execute function set_updated_at();

alter table users enable row level security;
alter table articles enable row level security;
alter table article_versions enable row level security;
alter table review_notes enable row level security;
alter table comments enable row level security;
alter table existing_content_index enable row level security;
