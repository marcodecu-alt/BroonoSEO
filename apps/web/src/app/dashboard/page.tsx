"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";
import { Article, isInProgress, listArticles, startArticle } from "@/lib/api";

const STATUS_STYLES: Record<string, string> = {
  researching: "bg-zinc-100 text-zinc-700",
  proposed: "bg-zinc-100 text-zinc-700",
  drafting: "bg-blue-100 text-blue-700",
  reviewing: "bg-blue-100 text-blue-700",
  awaiting_approval: "bg-amber-100 text-amber-800",
  approved: "bg-green-100 text-green-800",
  archived: "bg-zinc-100 text-zinc-500",
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
    <div className="flex flex-1 flex-col bg-zinc-50">
      <header className="flex items-center justify-between border-b border-zinc-200 bg-white px-8 py-4">
        <h1 className="text-lg font-semibold text-zinc-900">Broono SEO Pipeline</h1>
        <div className="flex items-center gap-4 text-sm text-zinc-600">
          <span>{session?.user.email}</span>
          <button
            onClick={handleSignOut}
            className="rounded-md border border-zinc-300 px-3 py-1.5 hover:bg-zinc-100"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="mx-auto w-full max-w-4xl flex-1 px-6 py-8">
        <form
          onSubmit={handleStart}
          className="mb-8 flex gap-3 rounded-lg border border-zinc-200 bg-white p-4"
        >
          <input
            type="text"
            placeholder="Optional topic seed (leave blank to let research agent decide)"
            value={topicSeed}
            onChange={(e) => setTopicSeed(e.target.value)}
            className="flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
          />
          <button
            type="submit"
            disabled={starting}
            className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50"
          >
            {starting ? "Starting..." : "Start new article"}
          </button>
        </form>

        {error && (
          <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
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
                  ? "bg-zinc-900 text-white"
                  : "bg-white text-zinc-600 border border-zinc-200 hover:bg-zinc-100"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        <div className="overflow-hidden rounded-lg border border-zinc-200 bg-white">
          {visibleArticles.length === 0 ? (
            <p className="p-8 text-center text-sm text-zinc-500">
              No articles here yet.
            </p>
          ) : (
            <ul className="divide-y divide-zinc-100">
              {visibleArticles.map((article) => (
                <li key={article.id}>
                  <Link
                    href={`/articles/${article.id}`}
                    className="flex items-center justify-between gap-4 px-5 py-4 hover:bg-zinc-50"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-zinc-900">
                        {article.brief_json?.title || "Untitled (research in progress)"}
                      </p>
                      <p className="truncate text-xs text-zinc-500">
                        {article.brief_json?.target_keyword || "No keyword yet"}
                      </p>
                    </div>
                    <span
                      className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${
                        STATUS_STYLES[article.status] || "bg-zinc-100 text-zinc-700"
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
