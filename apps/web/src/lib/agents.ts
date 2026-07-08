export type NodeAgentKey = "research_node" | "propose_node" | "draft_node" | "review_node";

export type AgentInfo = {
  name: string;
  role: string;
  emoji: string;
  colorClass: string; // Tailwind bg-* class for the avatar circle
  tagline: string;
  description: string;
};

export const ORCHESTRATOR: AgentInfo = {
  name: "Guido",
  role: "Orchestrator",
  emoji: "🐕",
  colorClass: "bg-ink",
  tagline: "Keeps the whole pipeline moving in order",
  description:
    "Guido isn't an AI agent that writes or thinks about content, it's the workflow itself, the thing that decides who goes next and what they're handed. When you start a new article, Guido calls Nicola, waits for the result, hands that to Simone, waits, hands Simone's brief to Celeste, waits, hands Celeste's draft to Sofia, waits, then stops and hands everything to you. It also carries state between agents, making sure Sofia actually sees Celeste's draft, and that a comment you leave carries your feedback into Celeste's next attempt. Guido doesn't judge quality or make creative decisions, it just makes sure the right work reaches the right agent in the right order, exactly once, never stuck in a loop.",
};

export const NODE_AGENTS: Record<NodeAgentKey, AgentInfo> = {
  research_node: {
    name: "Nicola",
    role: "Research agent",
    emoji: "🔍",
    colorClass: "bg-horizon",
    tagline: "Finds a topic worth writing about",
    description:
      "Nicola's job is to find a topic worth writing about. It uses live web search to look for what dog owners are actually typing into Google, specifically symptom- and problem-led searches (\"why is my dog limping\"), not the ingredient-led searches Broono already covers heavily (\"benefits of magnesium\"). Before finalizing anything, it checks its candidate ideas against Broono's own list of already-published articles and throws out anything that overlaps too closely. It comes back with 2-3 topic candidates, each with the exact keyword it's targeting and a written rationale covering apparent search demand and the content gap it fills. Nicola never writes anything, it only proposes what's worth writing about.",
  },
  propose_node: {
    name: "Simone",
    role: "Proposal agent",
    emoji: "🧭",
    colorClass: "bg-gold",
    tagline: "Picks the strongest topic and sets the direction",
    description:
      "Simone takes Nicola's 2-3 candidates and makes the call: picks the single strongest one and turns it into a concrete creative brief. It decides the working title, locks in the exact target keyword, writes a one-to-two sentence \"angle\" (the specific entry point and narrative shape the article will take), and figures out which Broono product category the article should tie back to (joint support, calming, digestive, skin/coat, etc). This is the green-light moment: everything downstream builds directly on the brief Simone hands off.",
  },
  draft_node: {
    name: "Celeste",
    role: "Draft agent",
    emoji: "🖋️",
    colorClass: "bg-ink-soft",
    tagline: "Writes the actual article",
    description:
      "Celeste writes the actual article. It reads Simone's brief, then fetches one of Broono's real existing articles live from broono.pet to study the voice, structure, and formatting conventions before writing a word. It produces a complete piece: a plain-language, keyword-forward title, a meta description, proper H2/H3 structure, a short FAQ, image briefs describing what visuals should go where, and a natural, non-pushy mention of the relevant Broono product, targeting 900-1,200 words so the article stays direct and scannable rather than padded. If Sofia flags something, or you leave a comment, Celeste is the one who gets that feedback and rewrites accordingly, always treating revision notes as requirements, not suggestions.",
  },
  review_node: {
    name: "Sofia",
    role: "Review agent",
    emoji: "🛡️",
    colorClass: "bg-peppermint",
    tagline: "Checks the draft before it reaches you",
    description:
      "Sofia is the quality and compliance check before anything reaches you. It reads Celeste's draft against a fixed checklist: unsupported health/medical claims (currently advisory-only, at your direction, since Broono is a supplement brand and this is genuinely sensitive), brand tone and voice consistency, on-page SEO basics, and duplication against Broono's already-published content. For each item it returns a clear pass/fail and a specific written explanation, never just a checkbox. Sofia runs exactly once per draft and always hands the result to you, whether everything passed or not, it never loops back to Celeste on its own. If you read its notes and decide a redraft is genuinely needed, leaving a comment is what sends the draft back to Celeste for exactly one more pass.",
  },
};

export function agentLabel(agent: NodeAgentKey): string {
  const info = NODE_AGENTS[agent];
  return `${info.name} — ${info.role}`;
}
