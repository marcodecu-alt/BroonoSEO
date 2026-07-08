-- Adds a 'failed' status and an error_message column so a pipeline crash
-- (billing, rate limit, network, etc.) is visible in the UI instead of
-- silently hanging the article at whatever status it was last in.

alter type article_status add value 'failed';

alter table articles add column error_message text;
