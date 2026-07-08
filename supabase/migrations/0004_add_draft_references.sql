-- Captures which URL(s) Celeste actually fetched for style reference when
-- writing a given draft version, so the Timeline can show her process, not
-- just her output.

alter table article_versions add column style_references jsonb default '[]'::jsonb;
