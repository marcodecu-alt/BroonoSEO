from .state import PipelineState


def research_node(state: PipelineState) -> PipelineState:
    """Find symptom/problem-led topic candidates, cross-checked against existing_content_index."""
    # TODO: search-based research + dedup against existing_content_index
    return {
        **state,
        "research_candidates": [],
        "status": "researching",
    }


def propose_node(state: PipelineState) -> PipelineState:
    """Pick the strongest research candidate and build a structured brief."""
    # TODO: select candidate, build brief via Claude
    return {
        **state,
        "brief": {
            "title": "",
            "target_keyword": "",
            "angle": "",
            "tied_product": "",
        },
        "status": "proposed",
    }


def draft_node(state: PipelineState) -> PipelineState:
    """Write the full article from the brief, using existing articles as style reference."""
    # TODO: draft via Claude, incorporating revision_notes if present
    return {
        **state,
        "draft_content": "",
        "status": "drafting",
    }


def review_node(state: PipelineState) -> PipelineState:
    """Check the draft against the fixed checklist."""
    # TODO: run checklist via Claude
    checklist = {
        "health_claims": {"passed": True, "note": ""},
        "tone": {"passed": True, "note": ""},
        "seo_basics": {"passed": True, "note": ""},
        "duplication": {"passed": True, "note": ""},
    }
    passed = all(item["passed"] for item in checklist.values())
    return {
        **state,
        "review_checklist": checklist,
        "review_passed": passed,
        "status": "awaiting_approval" if passed else "drafting",
    }


def review_router(state: PipelineState) -> str:
    return "awaiting_human_approval" if state.get("review_passed") else "draft_node"
