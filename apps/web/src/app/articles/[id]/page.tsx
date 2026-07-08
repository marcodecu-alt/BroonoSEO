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
  TimelineStep,
  agentLabel,
  approveArticle,
  commentOnArticle,
  currentStageLabel,
  exportUrl,
  getArticle,
  getArticleTimeline,
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

const AGENT_DOT: Record<TimelineStep["agent"], string> = {
  research_node: "bg-purple-500",
  propose_node: "bg-amber-500",
  draft_node: "bg-blue-500",
  review_node: "bg-green-500",
};

function TimelineStepCard({ step }: { step: TimelineStep }) {
  return (
    <div className="relative pl-6">
      <span
        className={`absolute left-0 top-1.5 h-2.5 w-2.5 rounded-full ${AGENT_DOT[step.agent]}`}
      />
      <div className="mb-1 flex items-center justify-between">
        <p className="text-sm font-semibold text-zinc-900">{agentLabel(step.agent)}</p>
        <p className="text-xs text-zinc-400">
          {new Date(step.created_at).toLocaleString()}
        </p>
      </div>

      {step.agent === "research_node" && (
        <ul className="space-y-2">
          {step.output.candidates.map((c, i) => (
            <li key={i} className="rounded-md bg-zinc-50 p-3 text-sm">
              <p className="font-medium text-zinc-900">{c.topic}</p>
              <p className="text-xs text-zinc-500">keyword: {c.target_keyword}</p>
              <p className="mt-1 text-zinc-600">{c.rationale}</p>
            </li>
          ))}
        </ul>
      )}

      {step.agent === "propose_node" && (
        <div className="rounded-md bg-zinc-50 p-3 text-sm">
          <p className="font-medium text-zinc-900">{step.output.title}</p>
          <p className="text-xs text-zinc-500">
            keyword: {step.output.target_keyword} · product: {step.output.tied_product}
          </p>
          <p className="mt-1 text-zinc-600">{step.output.angle}</p>
        </div>
      )}

      {step.agent === "draft_node" && (
        <div className="rounded-md bg-zinc-50 p-3 text-sm">
          <p className="mb-1 text-xs text-zinc-500">
            v{step.output.version_number} · {step.output.created_by.replace("_", " ")}
          </p>
          <p className="line-clamp-3 whitespace-pre-line text-zinc-600">
            {step.output.content}
          </p>
        </div>
      )}

      {step.agent === "review_node" && (
        <div className="rounded-md bg-zinc-50 p-3 text-sm">
          <p
            className={`mb-2 font-medium ${
              step.output.passed ? "text-green-700" : "text-red-700"
            }`}
          >
            {step.output.passed ? "Passed" : "Failed"}
          </p>
          <div className="space-y-1 text-xs text-zinc-600">
            <p>
              health claims: {step.output.checklist.health_claims.note}
            </p>
            <p>tone: {step.output.checklist.tone.note}</p>
            <p>seo basics: {step.output.checklist.seo_basics.note}</p>
            <p>duplication: {step.output.checklist.duplication.note}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ArticleDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [checked, setChecked] = useState(false);
  const [detail, setDetail] = useState<ArticleDetail | null>(null);
  const [timeline, setTimeline] = useState<TimelineStep[]>([]);
  const [activeTab, setActiveTab] = useState<"draft" | "timeline">("draft");
  const [error, setError] = useState<string | null>(null);
  const [commentText, setCommentText] = useState("");
  const [submittingComment, setSubmittingComment] = useState(false);
  const [approving, setApproving] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [data, steps] = await Promise.all([
        getArticle(params.id),
        getArticleTimeline(params.id),
      ]);
      setDetail(data);
      setTimeline(steps);
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
          <div className="mb-4 flex items-center justify-between">
            <h1 className="text-xl font-semibold text-zinc-900">
              {article.brief_json?.title || "Untitled"}
            </h1>
            <span className="shrink-0 rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700">
              {article.status.replace("_", " ")}
            </span>
          </div>

          <p
            className={`mb-4 rounded-md px-3 py-2 text-sm ${
              article.status === "failed"
                ? "bg-red-50 text-red-700"
                : inProgress
                ? "bg-blue-50 text-blue-700"
                : "bg-zinc-50 text-zinc-600"
            }`}
          >
            {currentStageLabel(article.status)}
            {inProgress && " This page refreshes automatically."}
          </p>

          {article.status === "failed" && article.error_message && (
            <div className="mb-6 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              <p className="font-medium">Error details:</p>
              <p className="mt-1">{article.error_message}</p>
            </div>
          )}

          <div className="mb-6 flex gap-1 border-b border-zinc-200">
            <button
              onClick={() => setActiveTab("draft")}
              className={`px-3 py-2 text-sm font-medium ${
                activeTab === "draft"
                  ? "border-b-2 border-zinc-900 text-zinc-900"
                  : "text-zinc-500 hover:text-zinc-700"
              }`}
            >
              Draft
            </button>
            <button
              onClick={() => setActiveTab("timeline")}
              className={`px-3 py-2 text-sm font-medium ${
                activeTab === "timeline"
                  ? "border-b-2 border-zinc-900 text-zinc-900"
                  : "text-zinc-500 hover:text-zinc-700"
              }`}
            >
              Timeline ({timeline.length})
            </button>
          </div>

          {activeTab === "draft" &&
            (latest_version ? (
              <article className="prose prose-zinc max-w-none prose-headings:font-semibold">
                <ReactMarkdown>{latest_version.content}</ReactMarkdown>
              </article>
            ) : (
              <p className="text-sm text-zinc-500">No draft yet.</p>
            ))}

          {activeTab === "timeline" &&
            (timeline.length === 0 ? (
              <p className="text-sm text-zinc-500">No steps yet.</p>
            ) : (
              <div className="space-y-6 border-l border-zinc-200 pl-1">
                {timeline.map((step, i) => (
                  <TimelineStepCard key={i} step={step} />
                ))}
              </div>
            ))}
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
