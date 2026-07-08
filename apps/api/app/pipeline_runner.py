import logging

from .graph.graph import pipeline_graph, resume_pipeline_graph
from .supabase_client import supabase

logger = logging.getLogger(__name__)


def _latest_version_number(article_id: str) -> int:
    resp = (
        supabase.table("article_versions")
        .select("version_number")
        .eq("article_id", article_id)
        .order("version_number", desc=True)
        .limit(1)
        .execute()
    )
    return resp.data[0]["version_number"] if resp.data else 0


def _persist_stream(article_id: str, stream, version_number: int):
    """Consume a LangGraph .stream(..., stream_mode='updates') iterator, persisting
    each node's output to Supabase as it happens. Marks the article as failed with
    the error message if anything raises, instead of silently hanging forever."""
    latest_version_id = None

    try:
        for update in stream:
            for node_name, partial in update.items():
                if node_name == "research_node":
                    supabase.table("pipeline_steps").insert(
                        {
                            "article_id": article_id,
                            "agent": "research_node",
                            "output_json": {
                                "candidates": partial["research_candidates"],
                                "searches": partial.get("research_searches", []),
                            },
                        }
                    ).execute()
                    supabase.table("articles").update(
                        {"status": "researching"}
                    ).eq("id", article_id).execute()

                elif node_name == "propose_node":
                    supabase.table("pipeline_steps").insert(
                        {
                            "article_id": article_id,
                            "agent": "propose_node",
                            "output_json": partial["brief"],
                        }
                    ).execute()
                    supabase.table("articles").update(
                        {"brief_json": partial["brief"], "status": "proposed"}
                    ).eq("id", article_id).execute()

                elif node_name == "draft_node":
                    version_number += 1
                    supabase.table("articles").update(
                        {"status": "reviewing"}
                    ).eq("id", article_id).execute()
                    version_resp = (
                        supabase.table("article_versions")
                        .insert(
                            {
                                "article_id": article_id,
                                "version_number": version_number,
                                "content": partial["draft_content"],
                                "created_by": "draft_agent",
                                "style_references": partial.get("draft_references", []),
                            }
                        )
                        .execute()
                    )
                    latest_version_id = version_resp.data[0]["id"]

                elif node_name == "review_node":
                    supabase.table("review_notes").insert(
                        {
                            "article_id": article_id,
                            "version_id": latest_version_id,
                            "checklist_json": partial["review_checklist"],
                            "passed": partial["review_passed"],
                        }
                    ).execute()
                    # Review never blocks: it always hands off to the human with
                    # its findings recorded, whether or not everything passed.
                    supabase.table("articles").update(
                        {"status": "awaiting_approval"}
                    ).eq("id", article_id).execute()
    except Exception as exc:
        logger.exception("Pipeline run failed for article %s", article_id)
        supabase.table("articles").update(
            {"status": "failed", "error_message": str(exc)}
        ).eq("id", article_id).execute()


def run_pipeline_and_persist(article_id: str, topic_seed: str | None):
    """Full pipeline: research -> propose -> draft -> review, single pass."""
    supabase.table("articles").update({"error_message": None}).eq(
        "id", article_id
    ).execute()

    stream = pipeline_graph.stream(
        {"topic_seed": topic_seed},
        config={"recursion_limit": 10},
        stream_mode="updates",
    )
    _persist_stream(article_id, stream, version_number=0)


def resume_pipeline_with_comment(article_id: str, comment_text: str):
    """Resume from draft_node with a human comment as revision context: one
    draft -> review pass, then back to the human."""
    supabase.table("articles").update({"error_message": None}).eq(
        "id", article_id
    ).execute()

    article_resp = supabase.table("articles").select("brief_json").eq(
        "id", article_id
    ).execute()
    brief = article_resp.data[0]["brief_json"]

    latest_version_resp = (
        supabase.table("article_versions")
        .select("content")
        .eq("article_id", article_id)
        .order("version_number", desc=True)
        .limit(1)
        .execute()
    )
    latest_content = latest_version_resp.data[0]["content"] if latest_version_resp.data else ""

    stream = resume_pipeline_graph.stream(
        {
            "brief": brief,
            "draft_content": latest_content,
            "revision_notes": comment_text,
        },
        config={"recursion_limit": 10},
        stream_mode="updates",
    )
    _persist_stream(article_id, stream, version_number=_latest_version_number(article_id))
