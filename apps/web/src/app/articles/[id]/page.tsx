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
  approveArticle,
  commentOnArticle,
  currentStageLabel,
  exportUrl,
  getArticle,
  getArticleTimeline,
  isInProgress,
} from "@/lib/api";
import { Logo } from "@/components/Logo";
import { NODE_AGENTS, getAvatarUrl } from "@/lib/agents";

function ChecklistRow({ label, item }: { label: string; item: ChecklistItem }) {
  return (
    <div className="flex items-start gap-3 py-2">
      <span
        className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
          item.passed ? "bg-peppermint/10 text-peppermint" : "bg-tangerine/10 text-tangerine"
        }`}
      >
        {item.passed ? "✓" : "✕"}
      </span>
      <div>
        <p className="text-sm font-medium text-ink">{label}</p>
        <p className="text-sm text-ink-soft">{item.note}</p>
      </div>
    </div>
  );
}

function TimelineStepCard({ step }: { step: TimelineStep }) {
  const agent = NODE_AGENTS[step.agent];
  return (
    <div className="relative pl-10">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={getAvatarUrl(agent)}
        alt={agent.name}
        className="absolute left-0 top-0 h-7 w-7 rounded-full"
      />
      <div className="mb-1 flex items-center justify-between">
        <p className="text-sm font-semibold text-ink">
          {agent.name} <span className="font-normal text-ink-soft">— {agent.role}</span>
        </p>
        <p className="text-xs text-ink-soft/70">
          {new Date(step.created_at).toLocaleString()}
        </p>
      </div>

      {step.agent === "research_node" && (
        <ul className="space-y-2">
          {step.output.candidates.map((c, i) => (
            <li key={i} className="rounded-md bg-cream p-3 text-sm">
              <p className="font-medium text-ink">{c.topic}</p>
              <p className="text-xs text-ink-soft">keyword: {c.target_keyword}</p>
              <p className="mt-1 text-ink-soft">{c.rationale}</p>
            </li>
          ))}
        </ul>
      )}

      {step.agent === "propose_node" && (
        <div className="rounded-md bg-cream p-3 text-sm">
          <p className="font-medium text-ink">{step.output.title}</p>
          <p className="text-xs text-ink-soft">
            keyword: {step.output.target_keyword} · product: {step.output.tied_product}
          </p>
          <p className="mt-1 text-ink-soft">{step.output.angle}</p>
        </div>
      )}

      {step.agent === "draft_node" && (
        <div className="rounded-md bg-cream p-3 text-sm">
          <p className="mb-1 text-xs text-ink-soft">
            v{step.output.version_number} · {step.output.created_by.replace("_", " ")}
          </p>
          <p className="line-clamp-3 whitespace-pre-line text-ink-soft">
            {step.output.content}
          </p>
        </div>
      )}

      {step.agent === "review_node" && (
        <div className="rounded-md bg-cream p-3 text-sm">
          <p
            className={`mb-2 font-medium ${
              step.output.passed ? "text-peppermint" : "text-tangerine"
            }`}
          >
            {step.output.passed ? "Passed" : "Failed"}
          </p>
          <div className="space-y-1 text-xs text-ink-soft">
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
    // Independent fetches: a timeline failure shouldn't block the draft/checklist
    // from loading, and vice versa.
    try {
      const data = await getArticle(params.id);
      setDetail(data);
      setError(null);
    } catch {
      setError("Couldn't load this article.");
    }
    try {
      const steps = await getArticleTimeline(params.id);
      setTimeline(steps);
    } catch {
      // Timeline is supplementary; leave it empty and let the tab say so.
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
      <div className="flex flex-1 items-center justify-center bg-cream">
        {error ? (
          <p className="text-sm text-tangerine">{error}</p>
        ) : (
          <p className="text-sm text-ink-soft">Loading...</p>
        )}
      </div>
    );
  }

  const { article, latest_version, versions, review_notes, comments } = detail;
  const latestReview = review_notes[0];
  const inProgress = isInProgress(article.status);

  return (
    <div className="flex flex-1 flex-col bg-cream">
      <header className="flex items-center justify-between border-b border-border bg-white px-8 py-4">
        <div className="flex items-center gap-4">
          <Link href="/dashboard">
            <Logo className="h-5 w-auto" />
          </Link>
          <Link href="/dashboard" className="text-sm text-ink-soft hover:text-ink">
            ← Dashboard
          </Link>
        </div>
        <div className="flex items-center gap-4 text-sm text-ink-soft">
          <Link href="/how-it-works" className="hover:text-ink">
            How it works
          </Link>
          <span>{session?.user.email}</span>
        </div>
      </header>

      <main className="mx-auto grid w-full max-w-5xl flex-1 grid-cols-1 gap-6 px-6 py-8 lg:grid-cols-[1fr_320px]">
        <div className="min-w-0 rounded-lg border border-border bg-white p-8">
          <div className="mb-4 flex items-center justify-between">
            <h1 className="text-xl font-semibold text-ink">
              {article.brief_json?.title || "Untitled"}
            </h1>
            <span className="shrink-0 rounded-full bg-ink/5 px-2.5 py-1 text-xs font-medium text-ink-soft">
              {article.status.replace("_", " ")}
            </span>
          </div>

          <p
            className={`mb-4 rounded-md px-3 py-2 text-sm ${
              article.status === "failed"
                ? "bg-tangerine/10 text-tangerine"
                : inProgress
                ? "bg-horizon/10 text-horizon"
                : "bg-cream text-ink-soft"
            }`}
          >
            {currentStageLabel(article.status)}
            {inProgress && " This page refreshes automatically."}
          </p>

          {article.status === "failed" && article.error_message && (
            <div className="mb-6 rounded-md bg-tangerine/10 px-3 py-2 text-sm text-tangerine">
              <p className="font-medium">Error details:</p>
              <p className="mt-1">{article.error_message}</p>
            </div>
          )}

          <div className="mb-6 flex gap-1 border-b border-border">
            <button
              onClick={() => setActiveTab("draft")}
              className={`px-3 py-2 text-sm font-medium ${
                activeTab === "draft"
                  ? "border-b-2 border-ink text-ink"
                  : "text-ink-soft hover:text-ink"
              }`}
            >
              Draft
            </button>
            <button
              onClick={() => setActiveTab("timeline")}
              className={`px-3 py-2 text-sm font-medium ${
                activeTab === "timeline"
                  ? "border-b-2 border-ink text-ink"
                  : "text-ink-soft hover:text-ink"
              }`}
            >
              Timeline ({timeline.length})
            </button>
          </div>

          {activeTab === "draft" &&
            (latest_version ? (
              <article className="prose prose-zinc max-w-none prose-headings:font-semibold prose-headings:text-ink prose-a:text-horizon">
                <ReactMarkdown>{latest_version.content}</ReactMarkdown>
              </article>
            ) : (
              <p className="text-sm text-ink-soft">No draft yet.</p>
            ))}

          {activeTab === "timeline" &&
            (timeline.length === 0 ? (
              <p className="text-sm text-ink-soft">No steps yet.</p>
            ) : (
              <div className="space-y-6">
                {timeline.map((step, i) => (
                  <TimelineStepCard key={i} step={step} />
                ))}
              </div>
            ))}
        </div>

        <div className="flex flex-col gap-6">
          <div className="rounded-lg border border-border bg-white p-5">
            <h2 className="mb-3 text-sm font-semibold text-ink">Review checklist</h2>
            {latestReview ? (
              <div className="divide-y divide-border">
                <ChecklistRow label="Health claims" item={latestReview.checklist_json.health_claims} />
                <ChecklistRow label="Tone" item={latestReview.checklist_json.tone} />
                <ChecklistRow label="SEO basics" item={latestReview.checklist_json.seo_basics} />
                <ChecklistRow label="Duplication" item={latestReview.checklist_json.duplication} />
              </div>
            ) : (
              <p className="text-sm text-ink-soft">No review yet.</p>
            )}
          </div>

          {article.status === "awaiting_approval" && (
            <button
              onClick={handleApprove}
              disabled={approving}
              className="rounded-md bg-peppermint px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
            >
              {approving ? "Approving..." : "Approve"}
            </button>
          )}

          {article.status === "approved" && (
            <button
              onClick={handleExport}
              className="rounded-md bg-horizon px-4 py-2 text-sm font-medium text-white hover:bg-horizon-dark"
            >
              Export Markdown
            </button>
          )}

          <div className="rounded-lg border border-border bg-white p-5">
            <h2 className="mb-3 text-sm font-semibold text-ink">
              Version history ({versions.length})
            </h2>
            <ul className="space-y-1 text-sm text-ink-soft">
              {versions.map((v) => (
                <li key={v.id}>
                  v{v.version_number} — {v.created_by.replace("_", " ")}
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-lg border border-border bg-white p-5">
            <h2 className="mb-3 text-sm font-semibold text-ink">Comments</h2>
            <ul className="mb-4 space-y-3 text-sm">
              {comments.length === 0 && (
                <li className="text-ink-soft">No comments yet.</li>
              )}
              {comments.map((c) => (
                <li key={c.id} className="rounded-md bg-cream p-3 text-ink-soft">
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
                className="rounded-md border border-border px-3 py-2 text-sm text-ink outline-none focus:border-horizon"
              />
              <button
                type="submit"
                disabled={submittingComment || !commentText.trim()}
                className="self-end rounded-md border border-border px-3 py-1.5 text-sm text-ink-soft hover:bg-cream disabled:opacity-50"
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
