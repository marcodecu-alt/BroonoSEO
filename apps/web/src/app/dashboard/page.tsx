"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";

export default function DashboardPage() {
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

  async function handleSignOut() {
    await supabase.auth.signOut();
    router.replace("/login");
  }

  if (!checked) {
    return null;
  }

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

      <main className="flex flex-1 items-center justify-center">
        <p className="text-zinc-500">
          No articles yet. Article list and pipeline controls go here.
        </p>
      </main>
    </div>
  );
}
