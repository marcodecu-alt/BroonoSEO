"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { Logo } from "@/components/Logo";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const { error } = await supabase.auth.signInWithPassword({ email, password });

    setLoading(false);

    if (error) {
      setError(error.message);
      return;
    }

    router.push("/dashboard");
  }

  return (
    <div className="flex flex-1 items-center justify-center bg-cream">
      <div className="flex w-full max-w-sm flex-col items-center gap-6">
        <Logo className="h-8 w-auto" />

        <form
          onSubmit={handleSubmit}
          className="flex w-full flex-col gap-4 rounded-lg border border-border bg-white p-8 shadow-sm"
        >
          <div>
            <h1 className="text-xl font-semibold text-ink">Sign in</h1>
            <p className="text-sm text-ink-soft">SEO Pipeline</p>
          </div>

          <label className="flex flex-col gap-1 text-sm text-ink-soft">
            Email
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="rounded-md border border-border px-3 py-2 text-sm text-ink outline-none focus:border-horizon"
            />
          </label>

          <label className="flex flex-col gap-1 text-sm text-ink-soft">
            Password
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="rounded-md border border-border px-3 py-2 text-sm text-ink outline-none focus:border-horizon"
            />
          </label>

          {error && <p className="text-sm text-tangerine">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="rounded-md bg-horizon px-4 py-2 text-sm font-medium text-white hover:bg-horizon-dark disabled:opacity-50"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
