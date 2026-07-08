from typing import TypedDict, Literal, Optional


class Brief(TypedDict):
    title: str
    target_keyword: str
    angle: str
    tied_product: str


class ReviewChecklistItem(TypedDict):
    passed: bool
    note: str


class ReviewChecklist(TypedDict):
    health_claims: ReviewChecklistItem
    tone: ReviewChecklistItem
    seo_basics: ReviewChecklistItem
    duplication: ReviewChecklistItem


class PipelineState(TypedDict, total=False):
    topic_seed: Optional[str]
    research_candidates: list[dict]
    research_searches: list[dict]
    brief: Brief
    draft_content: str
    draft_references: list[str]
    review_checklist: ReviewChecklist
    review_passed: bool
    revision_notes: Optional[str]
    status: Literal[
        "researching",
        "proposed",
        "drafting",
        "reviewing",
        "awaiting_approval",
        "approved",
        "archived",
        "failed",
    ]
