"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";
import { Logo } from "@/components/Logo";
import { ORCHESTRATOR, NODE_AGENTS, AgentInfo, getAvatarUrl } from "@/lib/agents";

const PIPELINE_ORDER: AgentInfo[] = [
  ORCHESTRATOR,
  NODE_AGENTS.research_node,
  NODE_AGENTS.propose_node,
  NODE_AGENTS.draft_node,
  NODE_AGENTS.review_node,
];

function AgentCard({ agent }: { agent: AgentInfo }) {
  return (
    <div className="rounded-lg border border-border bg-white p-6">
      <div className="mb-4 flex items-center gap-4">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={getAvatarUrl(agent)}
          alt={agent.name}
          className="h-14 w-14 shrink-0 rounded-full"
        />
        <div>
          <h2 className="text-lg font-semibold text-ink">{agent.name}</h2>
          <p className="text-sm text-ink-soft">{agent.role}</p>
        </div>
      </div>
      <p className="mb-3 text-sm font-medium text-ink-soft">{agent.tagline}</p>
      <ul className="space-y-1.5 text-sm text-ink-soft">
        {agent.bullets.map((b, i) => (
          <li key={i} className="flex gap-2">
            <span className="text-ink-soft/40">•</span>
            <span>{b}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function HowItWorksPage() {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [checked, setChecked] = useState(false);

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

  if (!checked) {
    return null;
  }

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
        <span className="text-sm text-ink-soft">{session?.user.email}</span>
      </header>

      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-ink">How it works</h1>
        <p className="mb-3 text-sm text-ink-soft">
          Every article passes through five agents, in order:
        </p>
        <ul className="mb-8 space-y-1.5 text-sm text-ink-soft">
          <li className="flex gap-2">
            <span className="text-ink-soft/40">•</span>
            <span>
              <strong>Guido</strong> (orchestrator) — kicks things off and hands work between
              the other four, one at a time
            </span>
          </li>
          <li className="flex gap-2">
            <span className="text-ink-soft/40">•</span>
            <span>
              <strong>Nicola</strong> — finds a topic
            </span>
          </li>
          <li className="flex gap-2">
            <span className="text-ink-soft/40">•</span>
            <span>
              <strong>Simone</strong> — turns it into a brief
            </span>
          </li>
          <li className="flex gap-2">
            <span className="text-ink-soft/40">•</span>
            <span>
              <strong>Celeste</strong> — writes the article
            </span>
          </li>
          <li className="flex gap-2">
            <span className="text-ink-soft/40">•</span>
            <span>
              <strong>Sofia</strong> — checks it before it lands in your dashboard, awaiting
              your approval
            </span>
          </li>
          <li className="flex gap-2">
            <span className="text-ink-soft/40">•</span>
            <span>
              You can watch each agent&apos;s actual output for any article on that
              article&apos;s <strong>Timeline</strong> tab
            </span>
          </li>
        </ul>

        <div className="flex flex-col gap-5">
          {PIPELINE_ORDER.map((agent) => (
            <AgentCard key={agent.name} agent={agent} />
          ))}
        </div>

        <div className="mt-8 rounded-lg border border-border bg-white p-6">
          <h2 className="mb-3 text-sm font-semibold text-ink">Then it&apos;s your turn</h2>
          <ul className="space-y-1.5 text-sm text-ink-soft">
            <li className="flex gap-2">
              <span className="text-ink-soft/40">•</span>
              <span>
                Once Sofia hands off a draft, it sits at <strong>awaiting approval</strong>{" "}
                until you act on it
              </span>
            </li>
            <li className="flex gap-2">
              <span className="text-ink-soft/40">•</span>
              <span>Read the draft and Sofia&apos;s checklist notes</span>
            </li>
            <li className="flex gap-2">
              <span className="text-ink-soft/40">•</span>
              <span>
                <strong>Approve</strong> it, ready to export as Markdown
              </span>
            </li>
            <li className="flex gap-2">
              <span className="text-ink-soft/40">•</span>
              <span>
                Or leave a <strong>comment</strong> with specific feedback, that sends it back
                to Celeste for exactly one more draft → review pass, then back to you
              </span>
            </li>
          </ul>
        </div>
      </main>
    </div>
  );
}
