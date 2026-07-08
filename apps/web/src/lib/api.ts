const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Brief = {
  title?: string;
  target_keyword?: string;
  angle?: string;
  tied_product?: string;
};

export type Article = {
  id: string;
  status: string;
  brief_json: Brief;
  created_at: string;
  updated_at: string;
};

export type ArticleVersion = {
  id: string;
  article_id: string;
  version_number: number;
  content: string;
  created_by: "draft_agent" | "review_agent" | "human";
  created_at: string;
};

export type ChecklistItem = { passed: boolean; note: string };

export type ReviewNote = {
  id: string;
  article_id: string;
  version_id: string;
  checklist_json: {
    health_claims: ChecklistItem;
    tone: ChecklistItem;
    seo_basics: ChecklistItem;
    duplication: ChecklistItem;
  };
  passed: boolean;
  created_at: string;
};

export type Comment = {
  id: string;
  article_id: string;
  version_id: string;
  user_id: string;
  comment_text: string;
  created_at: string;
};

export type ArticleDetail = {
  article: Article;
  latest_version: ArticleVersion | null;
  versions: ArticleVersion[];
  review_notes: ReviewNote[];
  comments: Comment[];
};

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

export function listArticles(): Promise<Article[]> {
  return fetch(`${API_URL}/articles`).then((r) => handle(r));
}

export function getArticle(id: string): Promise<ArticleDetail> {
  return fetch(`${API_URL}/articles/${id}`).then((r) => handle(r));
}

export function startArticle(topicSeed?: string): Promise<Article> {
  return fetch(`${API_URL}/articles/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic_seed: topicSeed || null }),
  }).then((r) => handle(r));
}

export function approveArticle(id: string): Promise<Article> {
  return fetch(`${API_URL}/articles/${id}/approve`, { method: "POST" }).then((r) =>
    handle(r)
  );
}

export function commentOnArticle(
  id: string,
  commentText: string,
  userId: string
): Promise<{ status: string }> {
  return fetch(`${API_URL}/articles/${id}/comment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ comment_text: commentText, user_id: userId }),
  }).then((r) => handle(r));
}

export function exportUrl(id: string): string {
  return `${API_URL}/articles/${id}/export`;
}

const IN_PROGRESS_STATUSES = new Set([
  "researching",
  "proposed",
  "drafting",
  "reviewing",
]);

export function isInProgress(status: string): boolean {
  return IN_PROGRESS_STATUSES.has(status);
}
