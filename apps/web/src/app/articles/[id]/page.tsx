"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";
import {
  ArticleDetail,
  ChecklistItem,
  approveArticle,
  commentOnArticle,
  exportUrl,
  getArticle,
  isInProgress,
} from "@/lib/api";

function ChecklistRow({ label, item }: { label: string; item: ChecklistItem }) {
  return (
    <div className="flex items-start gap-3 py-2">
      <span
        className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
          item.passed ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
        }`}
      >
        {item.passed ? "✓" : "✕"}
      </span>
      <div>
        <p className="text-sm font-medium text-zinc-900">{label}</p>
        <p className="text-sm text-zinc-600">{item.note}</p>
      </div>
    </div>
  );
}

export default function ArticleDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [checked, setChecked] = useState(false);
  const [detail, setDetail] = useState<ArticleDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [commentText, setCommentText] = useState("");
  const [submittingComment, setSubmittingComment] = useState(false);
  const [approving, setApproving] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const data = await getArticle(params.id);
      setDetail(data);
      setError(null);
    } catch {
      setError("Couldn't load this article.");
    }
  }, [params.id]);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        router.replace("/login");
        return;
      }
      setSession(data.session);
      setChecked(true);
    });
  }, [router]);

  useEffect(() => {
    if (!checked) return;
    refresh();
  }, [checked, refresh]);

  useEffect(() => {
    if (!checked || !detail) return;
    if (!isInProgress(detail.article.status)) return;
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [checked, detail, refresh]);

  async function handleApprove() {
    setApproving(true);
    try {
      await approveArticle(params.id);
      await refresh();
    } catch {
      setError("Couldn't approve this article.");
    } finally {
      setApproving(false);
    }
  }

  async function handleComment(e: React.FormEvent) {
    e.preventDefault();
    if (!commentText.trim() || !session) return;
    setSubmittingComment(true);
    try {
      await commentOnArticle(params.id, commentText, session.user.id);
      setCommentText("");
      await refresh();
    } catch {
      setError("Couldn't submit that comment.");
    } finally {
      setSubmittingComment(false);
    }
  }

  async function handleExport() {
    const res = await fetch(exportUrl(params.id));
    if (!res.ok) {
      setError("Couldn't export this article, is it approved?");
      return;
    }
    const text = await res.text();
    const blob = new Blob([text], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${(detail?.article.brief_json?.target_keyword || "article").replace(/\s+/g, "-")}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (!checked || !detail) {
    return (
      <div className="flex flex-1 items-center justify-center bg-zinc-50">
        {error ? (
          <p className="text-sm text-red-600">{error}</p>
        ) : (
          <p className="text-sm text-zinc-500">Loading...</p>
        )}
      </div>
    );
  }

  const { article, latest_version, versions, review_notes, comments } = detail;
  const latestReview = review_notes[0];
  const inProgress = isInProgress(article.status);

  return (
    <div className="flex flex-1 flex-col bg-zinc-50">
      <header className="flex items-center justify-between border-b border-zinc-200 bg-white px-8 py-4">
        <Link href="/dashboard" className="text-sm text-zinc-500 hover:text-zinc-900">
          ← Dashboard
        </Link>
        <span className="text-sm text-zinc-600">{session?.user.email}</span>
      </header>

      <main className="mx-auto grid w-full max-w-5xl flex-1 grid-cols-1 gap-6 px-6 py-8 lg:grid-cols-[1fr_320px]">
        <div className="min-w-0 rounded-lg border border-zinc-200 bg-white p-8">
          <div className="mb-6 flex items-center justify-between">
            <h1 className="text-xl font-semibold text-zinc-900">
              {article.brief_json?.title || "Untitled"}
            </h1>
            <span className="shrink-0 rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700">
              {article.status.replace("_", " ")}
            </span>
          </div>

          {inProgress && (
            <p className="mb-6 rounded-md bg-blue-50 px-3 py-2 text-sm text-blue-700">
              Pipeline is running ({article.status.replace("_", " ")}...). This page
              refreshes automatically.
            </p>
          )}

          {article.status === "failed" && (
            <div className="mb-6 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              <p className="font-medium">Pipeline run failed.</p>
              <p className="mt-1">{article.error_message || "No error details recorded."}</p>
            </div>
          )}

          {latest_version ? (
            <article className="prose prose-zinc max-w-none prose-headings:font-semibold">
              <ReactMarkdown>{latest_version.content}</ReactMarkdown>
            </article>
          ) : (
            <p className="text-sm text-zinc-500">No draft yet.</p>
          )}
        </div>

        <div className="flex flex-col gap-6">
          <div className="rounded-lg border border-zinc-200 bg-white p-5">
            <h2 className="mb-3 text-sm font-semibold text-zinc-900">Review checklist</h2>
            {latestReview ? (
              <div className="divide-y divide-zinc-100">
                <ChecklistRow label="Health claims" item={latestReview.checklist_json.health_claims} />
                <ChecklistRow label="Tone" item={latestReview.checklist_json.tone} />
                <ChecklistRow label="SEO basics" item={latestReview.checklist_json.seo_basics} />
                <ChecklistRow label="Duplication" item={latestReview.checklist_json.duplication} />
              </div>
            ) : (
              <p className="text-sm text-zinc-500">No review yet.</p>
            )}
          </div>

          {article.status === "awaiting_approval" && (
            <button
              onClick={handleApprove}
              disabled={approving}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              {approving ? "Approving..." : "Approve"}
            </button>
          )}

          {article.status === "approved" && (
            <button
              onClick={handleExport}
              className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700"
            >
              Export Markdown
            </button>
          )}

          <div className="rounded-lg border border-zinc-200 bg-white p-5">
            <h2 className="mb-3 text-sm font-semibold text-zinc-900">
              Version history ({versions.length})
            </h2>
            <ul className="space-y-1 text-sm text-zinc-600">
              {versions.map((v) => (
                <li key={v.id}>
                  v{v.version_number} — {v.created_by.replace("_", " ")}
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-lg border border-zinc-200 bg-white p-5">
            <h2 className="mb-3 text-sm font-semibold text-zinc-900">Comments</h2>
            <ul className="mb-4 space-y-3 text-sm">
              {comments.length === 0 && (
                <li className="text-zinc-500">No comments yet.</li>
              )}
              {comments.map((c) => (
                <li key={c.id} className="rounded-md bg-zinc-50 p-3 text-zinc-700">
                  {c.comment_text}
                </li>
              ))}
            </ul>
            <form onSubmit={handleComment} className="flex flex-col gap-2">
              <textarea
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder="Leave feedback to trigger a revision..."
                rows={3}
                className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
              />
              <button
                type="submit"
                disabled={submittingComment || !commentText.trim()}
                className="self-end rounded-md border border-zinc-300 px-3 py-1.5 text-sm hover:bg-zinc-100 disabled:opacity-50"
              >
                {submittingComment ? "Sending..." : "Send"}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}
