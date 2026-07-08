"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";
import { Article, isInProgress, listArticles, startArticle } from "@/lib/api";
import { Logo } from "@/components/Logo";

const STATUS_STYLES: Record<string, string> = {
  researching: "bg-ink/5 text-ink-soft",
  proposed: "bg-ink/5 text-ink-soft",
  drafting: "bg-horizon/10 text-horizon",
  reviewing: "bg-horizon/10 text-horizon",
  awaiting_approval: "bg-gold/15 text-gold-dark",
  approved: "bg-peppermint/10 text-peppermint",
  archived: "bg-ink/5 text-ink-soft",
  failed: "bg-tangerine/10 text-tangerine",
};

const FILTERS = [
  { key: "all", label: "All" },
  { key: "in_progress", label: "In progress" },
  { key: "awaiting_approval", label: "Needs your review" },
  { key: "approved", label: "Approved" },
] as const;

type FilterKey = (typeof FILTERS)[number]["key"];

function matchesFilter(article: Article, filter: FilterKey): boolean {
  if (filter === "all") return true;
  if (filter === "in_progress") return isInProgress(article.status);
  return article.status === filter;
}

export default function DashboardPage() {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [checked, setChecked] = useState(false);
  const [articles, setArticles] = useState<Article[]>([]);
  const [filter, setFilter] = useState<FilterKey>("all");
  const [topicSeed, setTopicSeed] = useState("");
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await listArticles();
      setArticles(data);
      setError(null);
    } catch {
      setError("Couldn't reach the API. Is the backend running?");
    }
  }, []);

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
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [checked, refresh]);

  async function handleSignOut() {
    await supabase.auth.signOut();
    router.replace("/login");
  }

  async function handleStart(e: React.FormEvent) {
    e.preventDefault();
    setStarting(true);
    setError(null);
    try {
      await startArticle(topicSeed || undefined);
      setTopicSeed("");
      await refresh();
    } catch {
      setError("Couldn't start a new article.");
    } finally {
      setStarting(false);
    }
  }

  if (!checked) {
    return null;
  }

  const visibleArticles = articles.filter((a) => matchesFilter(a, filter));

  return (
    <div className="flex flex-1 flex-col bg-cream">
      <header className="flex items-center justify-between border-b border-border bg-white px-8 py-4">
        <div className="flex items-center gap-3">
          <Logo />
          <span className="text-sm text-ink-soft">SEO Pipeline</span>
        </div>
        <div className="flex items-center gap-4 text-sm text-ink-soft">
          <Link href="/how-it-works" className="hover:text-ink">
            How it works
          </Link>
          <span>{session?.user.email}</span>
          <button
            onClick={handleSignOut}
            className="rounded-md border border-border px-3 py-1.5 hover:bg-cream"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="mx-auto w-full max-w-4xl flex-1 px-6 py-8">
        <form
          onSubmit={handleStart}
          className="mb-8 flex gap-3 rounded-lg border border-border bg-white p-4"
        >
          <input
            type="text"
            placeholder="Optional topic seed (leave blank to let research agent decide)"
            value={topicSeed}
            onChange={(e) => setTopicSeed(e.target.value)}
            className="flex-1 rounded-md border border-border px-3 py-2 text-sm text-ink outline-none focus:border-horizon"
          />
          <button
            type="submit"
            disabled={starting}
            className="rounded-md bg-horizon px-4 py-2 text-sm font-medium text-white hover:bg-horizon-dark disabled:opacity-50"
          >
            {starting ? "Starting..." : "Start new article"}
          </button>
        </form>

        {error && (
          <p className="mb-4 rounded-md bg-tangerine/10 px-3 py-2 text-sm text-tangerine">
            {error}
          </p>
        )}

        <div className="mb-4 flex gap-2">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`rounded-full px-3 py-1.5 text-sm font-medium ${
                filter === f.key
                  ? "bg-ink text-white"
                  : "bg-white text-ink-soft border border-border hover:bg-cream"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        <div className="overflow-hidden rounded-lg border border-border bg-white">
          {visibleArticles.length === 0 ? (
            <p className="p-8 text-center text-sm text-ink-soft">
              No articles here yet.
            </p>
          ) : (
            <ul className="divide-y divide-border">
              {visibleArticles.map((article) => (
                <li key={article.id}>
                  <Link
                    href={`/articles/${article.id}`}
                    className="flex items-center justify-between gap-4 px-5 py-4 hover:bg-cream"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-ink">
                        {article.brief_json?.title || "Untitled (research in progress)"}
                      </p>
                      <p className="truncate text-xs text-ink-soft">
                        {article.brief_json?.target_keyword || "No keyword yet"}
                      </p>
                    </div>
                    <span
                      className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${
                        STATUS_STYLES[article.status] || "bg-ink/5 text-ink-soft"
                      }`}
                    >
                      {article.status.replace("_", " ")}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>
    </div>
  );
}
