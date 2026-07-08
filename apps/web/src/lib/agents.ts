export type NodeAgentKey = "research_node" | "propose_node" | "draft_node" | "review_node";

export type AgentInfo = {
  name: string;
  role: string;
  bgHex: string; // hex without '#', used as the avatar background color
  tagline: string;
  bullets: string[];
};

function avatarUrl(seed: string, bgHex: string): string {
  return `https://api.dicebear.com/9.x/avataaars/svg?seed=${encodeURIComponent(
    seed
  )}&backgroundColor=${bgHex}`;
}

export const ORCHESTRATOR: AgentInfo = {
  name: "Guido",
  role: "Orchestrator",
  bgHex: "03183f",
  tagline: "Keeps the whole pipeline moving in order",
  bullets: [
    "Not an AI agent itself, it's the workflow that runs the other four in order",
    "Calls Nicola → Simone → Celeste → Sofia, one at a time, waiting for each to finish",
    "Carries state between agents, e.g. makes sure Sofia sees Celeste's actual draft",
    "Doesn't judge quality or write anything, just keeps things moving, exactly once, no loops",
  ],
};

export const NODE_AGENTS: Record<NodeAgentKey, AgentInfo> = {
  research_node: {
    name: "Nicola",
    role: "Research agent",
    bgHex: "0559c6",
    tagline: "Finds a topic worth writing about",
    bullets: [
      "Searches the web for what dog owners actually type into Google",
      "Focuses on symptom/problem-led queries (\"why is my dog limping\"), not ingredient-led ones",
      "Checks candidates against Broono's already-published articles to avoid duplicates",
      "Returns 2-3 topic candidates with keyword + rationale, never writes content itself",
    ],
  },
  propose_node: {
    name: "Simone",
    role: "Proposal agent",
    bgHex: "d9a441",
    tagline: "Picks the strongest topic and sets the direction",
    bullets: [
      "Picks the single strongest topic from Nicola's candidates",
      "Builds the brief: working title, target keyword, angle, and which Broono product it ties to",
      "This is the green light, everything downstream builds on this brief",
    ],
  },
  draft_node: {
    name: "Celeste",
    role: "Draft agent",
    bgHex: "244064",
    tagline: "Writes the actual article",
    bullets: [
      "Fetches a real Broono article first, to match voice and structure",
      "Writes the full article: title, meta description, H2/H3s, FAQ, image briefs",
      "Targets 900-1,200 words, leads with the answer, avoids generic openers",
      "Treats revision notes (from Sofia or your comments) as requirements, not suggestions",
    ],
  },
  review_node: {
    name: "Sofia",
    role: "Review agent",
    bgHex: "079b72",
    tagline: "Checks the draft before it reaches you",
    bullets: [
      "Checks the draft against a fixed checklist: health claims, tone, SEO basics, duplication",
      "Health claims is advisory-only (your call), the rest can still show as failed",
      "Gives a specific written reason for every pass/fail, never just a checkbox",
      "Runs once and always hands off to you, never loops back to Celeste on its own",
    ],
  },
};

export function getAvatarUrl(agent: AgentInfo): string {
  return avatarUrl(agent.name, agent.bgHex);
}
